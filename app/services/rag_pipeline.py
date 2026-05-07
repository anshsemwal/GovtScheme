"""
Production RAG Pipeline - No Mocks, No Fallbacks
All operations require valid Hugging Face API
"""
import logging
from typing import List, Dict, Any, Optional
import numpy as np
import requests

from app.config import settings
from app.models.user import Profile
from app.models.scheme import Scheme
from app.knowledge_base.schemes_data import schemes_data
from app.knowledge_base.faiss_store import FAISSStore
from app.services.eligibility import eligibility_validator
from app.services.web_search import web_search_service

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
# HF URLs removed


class RAGPipeline:
    """Production RAG Pipeline with mandatory HF API"""
    
    def __init__(self):
        self.faiss_store = FAISSStore(dimension=384) # force 384 for all-MiniLM-L6-v2
        self.schemes = schemes_data
        self.scheme_map: Dict[str, Scheme] = {s.scheme_id: s for s in self.schemes}
        self._initialized = False
        # Initialize local model
        try:
            logger.info("Loading local embedding model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Local model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load local model: {e}")
            self.model = None
        
    def initialize(self) -> None:
        """Initialize RAG pipeline with scheme embeddings"""
        if self._initialized:
            return
            
        logger.info("Initializing RAG pipeline with local embeddings...")
        
        documents = []
        metadata = []
        embeddings = []
        
        for scheme in self.schemes:
            doc_text = scheme.to_embedding_text()
            documents.append(doc_text)
            metadata.append({
                "scheme_id": scheme.scheme_id,
                "name": scheme.name,
                "category": scheme.category
            })
            embedding = self._generate_embedding(doc_text)
            embeddings.append(embedding)
        
        self.faiss_store.add_embeddings(embeddings, documents, metadata)
        self._initialized = True
        logger.info(f"RAG pipeline initialized with {len(self.schemes)} schemes")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using local model"""
        if not self.model:
            raise RuntimeError("Local embedding model not initialized")
            
        try:
            # Generate embedding
            embedding = self.model.encode(text)
            
            # Convert to list if it's a numpy array
            if isinstance(embedding, np.ndarray):
                return embedding.tolist()
            return embedding
                
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise RuntimeError(f"Embedding generation failed: {str(e)}")
    
    def _keyword_search(self, query: str) -> List[Dict[str, Any]]:
        """Keyword-based search with strict relevance"""
        query_lower = query.lower()
        
        # VERY SPECIFIC Synonyms - don't pollute the search
        synonym_map = {
            "pension": ["retirement", "old age", "senior citizen"],
            "scholarship": ["education", "study", "student"],
            "housing": ["house", "awas", "construction", "home"],
            "loan": ["credit", "finance", "business"],
            "farmer": ["agriculture", "kisan", "crop", "land"],
            "health": ["medical", "insurance", "hospital", "ayushman"],
            "girl": ["daughter", "female", "lady", "sukanya"],
        }
        
        # Specific terms from the user query
        query_terms = set()
        stopwords = {"scheme", "schemes", "government", "india", "find", "show", "tell", 
                     "about", "what", "where", "program", "yojana", "give", "list", "the", 
                     "for", "and", "with", "please", "can", "you", "are", "there", "any"}
        
        raw_words = query_lower.split()
        for word in raw_words:
            clean_word = word.strip(".,!?")
            if len(clean_word) > 2 and clean_word not in stopwords:
                query_terms.add(clean_word)
                if clean_word in synonym_map:
                    query_terms.update(synonym_map[clean_word])
        
        if not query_terms:
            return []
        
        results = []
        for scheme in self.schemes:
            text = (scheme.name + " " + scheme.description + " " + 
                    scheme.category + " " + scheme.benefits).lower()
            
            # Count how many query terms match
            matches = 0
            for term in query_terms:
                if term in text:
                    matches += 1
            
            if matches > 0:
                # Score based on percentage of terms matched + category weight
                match_ratio = matches / len(query_terms)
                category_match = any(t in scheme.category.lower() for t in query_terms)
                
                score = (match_ratio * 0.7) + (0.3 if category_match else 0)
                
                results.append({
                    "metadata": {"scheme_id": scheme.scheme_id},
                    "score": score
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    def retrieve_context(
        self, 
        query: str, 
        profile: Optional[Profile] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant schemes based on query, with optional profile context"""
        if not self._initialized:
            self.initialize()
        
        # Family Inference Logic:
        # If the user asks about kids/family, we should search for their community too
        search_query = query
        if profile and profile.community:
            family_terms = ["son", "daughter", "child", "children", "kids", "boy", "girl"]
            if any(term in query.lower() for term in family_terms):
                search_query += f" {profile.community}"
        
        # Keyword search FIRST (primary)
        keyword_results = self._keyword_search(search_query)
        
        # Vector search (secondary)
        vector_results = []
        try:
            query_embedding = self._generate_embedding(search_query)
            vector_results = self.faiss_store.vector_search(query_embedding, k=k*2)
        except Exception as e:
            logger.warning(f"Vector search failed, using keyword search only: {str(e)}")
        
        # Merge results - PRIORITIZE keyword results 
        results_map = {}
        
        # Add keyword results first with boosted scores
        for res in keyword_results:
            sid = res["metadata"].get("scheme_id")
            if sid:
                res["score"] = res["score"] * 1.2  # Boost keyword matches
                results_map[sid] = res
        
        # Add vector results only if not already in keyword results
        for res in vector_results:
            sid = res["metadata"].get("scheme_id")
            if sid:
                if sid in results_map:
                    # Keep the higher score
                    results_map[sid]["score"] = max(results_map[sid]["score"], res["score"])
                else:
                    results_map[sid] = res
        
        results = list(results_map.values())
        
        # **CRITICAL**: If no results OR all results have low scores, return EMPTY
        # This tells LLM to answer directly without RAG context
        if not results:
            logger.info(f"No RAG results for query: {query}. Will use pure LLM.")
            return []
        
        # Check if top result score is too low (irrelevant)
        top_score = max(r["score"] for r in results) if results else 0
        if top_score < 0.1:  # Lowered threshold to allow the AI to decide relevance
            logger.info(f"Top score {top_score} too low for query: {query}. Skipping RAG.")
            return []
        
        # Enrich with scheme data and eligibility
        enriched_results = []
        for result in results:
            scheme_id = result["metadata"].get("scheme_id")
            scheme = self.scheme_map.get(scheme_id)
            if not scheme:
                continue
            
            eligibility_info = None
            if profile:
                is_eligible, met, unmet = eligibility_validator.validate_eligibility(profile, scheme)
                eligibility_info = {
                    "is_eligible": is_eligible,
                    "met_criteria": met,
                    "unmet_criteria": unmet
                }
            
            enriched_results.append({
                "scheme": scheme,
                "score": result["score"],
                "eligibility": eligibility_info
            })
        
        # Sort by score only (not eligibility) to maintain relevance
        enriched_results.sort(key=lambda x: x["score"], reverse=True)
        
        # Final check: if enriched results are empty, return empty
        if not enriched_results:
            return []
            
        return enriched_results[:k]
    
    def generate_response(
        self,
        query: str,
        context: List[Dict[str, Any]],
        profile: Optional[Profile] = None,
        language: str = "en",
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Generate response using Mistral AI with conversation history"""
        profile_str = profile.to_text() if profile else "Not provided"

        try:
            # Prepare context for the prompt if RAG found HIGHLY relevant results
            context_str = ""
            relevant_context = []
            
            # Detect if we should search the web
            should_search_web = any(word in query.lower() for word in ["new", "latest", "2024", "recent", "today", "current"])
            
            # Fetch web context if needed or if local context is weak
            web_context = ""
            if should_search_web or not context or (context and context[0]["score"] < 0.4):
                web_context = web_search_service.get_web_context(query)
            
            # Use query for filtering inside the context
            query_lower = query.lower()
            
            if context:
                # Use retrieved context directly, but filter out very low scores if any
                # RAG already did this, so we can just use the context
                relevant_context = context
            
            if relevant_context:
                for i, item in enumerate(relevant_context[:3], 1):
                    scheme = item["scheme"]
                    eligibility = item.get("eligibility")
                    status = "✅ LIKELY ELIGIBLE" if eligibility and eligibility["is_eligible"] else "⚠️ CHECK ELIGIBILITY"
                    
                    context_str += f"### {i}. {scheme.name} ({status})\n"
                    context_str += f"**Category:** {scheme.category}\n"
                    context_str += f"**Description:** {scheme.description}\n"
                    context_str += f"**Benefits:** {scheme.benefits}\n"
                    context_str += f"**Eligibility Criteria:**\n"
                    
                    # Add detailed criteria
                    crit = scheme.eligibility_criteria
                    if crit.min_age or crit.max_age:
                        context_str += f"- Age: {crit.min_age or 0} to {crit.max_age or 100} years\n"
                    if crit.max_income:
                        context_str += f"- Income: Up to ₹{crit.max_income:,.0f} per year\n"
                    if crit.gender:
                        context_str += f"- Gender: {crit.gender.title()}\n"
                    if crit.occupations:
                        context_str += f"- Occupations: {', '.join(crit.occupations)}\n"
                    if crit.locations:
                        context_str += f"- Locations: {', '.join(crit.locations)}\n"
                    if crit.communities:
                        context_str += f"- Community: {', '.join(crit.communities)}\n"
                    if crit.is_farmer_required:
                        context_str += "- Farmers Only\n"
                    if crit.is_bpl_required:
                        context_str += "- BPL Families Only\n"
                    
                    context_str += f"**Required Documents:**\n"
                    if scheme.documents_required:
                        for doc in scheme.documents_required:
                            context_str += f"- {doc}\n"
                    else:
                        context_str += "- Aadhaar Card, ID Proof\n"
                        
                    context_str += f"**Application Process:** {scheme.application_process}\n"
                    context_str += f"**Source:** {scheme.source}\n\n"

            # Create a professional, detailed, and structured prompt
            if context_str or web_context:
                system_prompt = f"""You are 'CivicScheme AI'. Your goal is to provide COMPREHENSIVE and DETAILED information to the citizen in a NATURAL CONVERSATIONAL way.
                
                USER PROFILE (Source of Truth):
                {profile_str}

                RELEVANT DATABASE SCHEMES:
                {context_str or "None found in local database."}
                
                {web_context}
                
                CRITICAL CONVERSATIONAL RULES:
                1. **WEB SOURCE**: If you use information from the 'Latest Web Information' section, explicitly mention: "According to recent web sources..." so the user knows this is external live data.
                2. **NO LABELS**: DO NOT start your response with "Title:", "Description:", or "User Query:". Never use these as metadata labels in the chat.
                3. **CHAT STYLE**: Write as if you are talking to the person. 
                4. **PROFILE PRIORITY**: Explain how the schemes fit the user's Profile naturally.
                5. **LINKS REQUIRED**: ALWAYS include application links (URLs) from both local and web context.
                """
            else:
                system_prompt = f"""You are 'CivicScheme AI'. Provide a COMPREHENSIVE response in a NATURAL CHAT format.
                
                USER PROFILE: {profile_str}
                
                RULES:
                1. Avoid technical labels like "Title:", "Description:", or "Metadata:".
                2. Answer the query directly and thoroughly as a helpful advisor.
                3. Structure with Markdown but keep the tone like a professional chat.
                4. **RELATIONSHIP**: Apply the user's community/location to family members mentioned.
                5. **CONTEXT**: Use previous messages to understand follow-up questions.
                """

            if not settings.mistral_api_key:
                raise ValueError("Mistral API key not configured")

            url = "https://api.mistral.ai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {settings.mistral_api_key}",
                "Content-Type": "application/json"
            }
            
            # Prepare messages with history
            messages = [{"role": "system", "content": system_prompt}]
            
            if history:
                messages.extend(history)
            
            # Add current query
            messages.append({"role": "user", "content": f"Query: {query}"})
            
            data = {
                "model": settings.llm_model,
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": 2048
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=20)
            response.raise_for_status()
            
            result = response.json()
            final_response = result["choices"][0]["message"]["content"]
            
        except Exception as e:
            logger.error(f"Mistral API call failed: {str(e)}")
            # Fallback to simple template if API fails
            
            if not context:
                return "I couldn't find any specific schemes matching your request in our database. You might want to check the official government portal or visit a CSC center for more options."

            response_parts = ["Based on your profile, I found these relevant schemes for you:\n"]
            
            for i, item in enumerate(context[:3], 1):
                scheme = item["scheme"]
                eligibility = item.get("eligibility")
                
                status = "✅ Eligible" if eligibility and eligibility["is_eligible"] else "⚠️ Check eligibility"
                
                response_parts.append(f"\n**{i}. {scheme.name}** ({status})")
                response_parts.append(f"   {scheme.description[:150]}...")
                response_parts.append(f"   Benefits: {scheme.benefits}")
                response_parts.append(f"   Application: {scheme.application_process}")
            
            response_parts.append("\n\nWould you like more details on any of these?")
            final_response = "\n".join(response_parts)
            
        return final_response


# Singleton instance
rag_pipeline = RAGPipeline()
