
import time
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from app.services.rag_pipeline import RAGPipeline
from app.models.user import Profile
import logging

# Disable heavy logging for the benchmark
logging.getLogger("app.services.rag_pipeline").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

def run_benchmark():
    print("Initializing RAG Pipeline...")
    rag = RAGPipeline()
    rag.initialize()
    print("RAG Pipeline Initialized.")

    # Test Data: Queries of varying complexity
    queries = [
        "education loan",
        "scholarship for girls",
        "farmers subsidy for tractors",
        "pension for senior citizens",
        "health insurance for poor families",
        "startup funding for youth",
        "housing scheme in rural areas",
        "widow pension details",
        "employment guarantee scheme",
        "solar panel subsidy"
    ]

    # Test Profile
    profile = Profile(
        age=25,
        gender="male",
        income=100000,
        community="OBC",
        location="Maharashtra",
        occupation="Student",
        is_farmer=False,
        is_bpl=True
    )

    results = []

    print("\nStarting Benchmark...")
    print(f"{'Query':<35} | {'Latency (ms)':<15} | {'Schemes Found':<15}")
    print("-" * 70)

    for query in queries:
        # Warmup
        rag.retrieve_context(query, profile)

        # Measure
        start_time = time.time()
        # Run 10 times to get average
        iterations = 10
        for _ in range(iterations):
            rag.retrieve_context(query, profile)
        end_time = time.time()
        
        avg_time_ms = ((end_time - start_time) / iterations) * 1000
        result_count = len(rag.retrieve_context(query, profile))
        
        results.append({
            "Query": query,
            "Latency (ms)": avg_time_ms,
            "Results Found": result_count
        })

        print(f"{query:<35} | {avg_time_ms:.2f} ms        | {result_count:<15}")

    # Create DataFrame for plotting
    df = pd.DataFrame(results)

    # Plotting
    plt.figure(figsize=(12, 6))
    
    # 1. Bar Chart for Latency
    sns.set_style("whitegrid")
    ax = sns.barplot(x="Latency (ms)", y="Query", data=df, palette="viridis")
    
    plt.title("RAG Retrieval Performance Latency", fontsize=16)
    plt.xlabel("Average Latency (ms)", fontsize=12)
    plt.ylabel("Test Query", fontsize=12)
    
    # Add value labels
    for i in ax.containers:
        ax.bar_label(i, fmt='%.1f ms', padding=3)

    plt.tight_layout()
    output_file = "rag_performance_graph.png"
    plt.savefig(output_file, dpi=300)
    print(f"\nGraph saved to: {output_file}")
    
    # Optional: Save raw data
    df.to_csv("rag_benchmark_results.csv", index=False)
    print("Results saved to: rag_benchmark_results.csv")

if __name__ == "__main__":
    run_benchmark()
