import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Cấu hình đường dẫn thư mục
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH_1 = PROJECT_ROOT / "data_local" / "raw" / "text_comment_1.csv"
DATA_PATH_2 = PROJECT_ROOT / "data_local" / "raw" / "text_comment_2.csv"
OUTPUT_DIR = PROJECT_ROOT / "images" / "eda"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def analyze_data_quality(df):
    print("--- 1. KHẢO SÁT CHẤT LƯỢNG DỮ LIỆU ---")
    print(f"Tổng số bản ghi: {len(df)}")
    print("\nKiểm tra dữ liệu thiếu (Null/NaN):")
    print(df.isnull().sum())
    
    print("\nKiểm tra trùng lặp:")
    duplicates = df.duplicated().sum()
    print(f"Số lượng bản ghi trùng lặp: {duplicates}")
    
    # Chuẩn hóa (nếu có null thì drop)
    df = df.dropna().drop_duplicates()
    print(f"Số bản ghi sau khi làm sạch: {len(df)}")
    return df

def analyze_label_distribution_by_source(df):
    print("\n---KHẢO SÁT PHÂN BỐ NHÃN THEO NGUỒN ---")
    # Group by source and label
    grouped = df.groupby(['source', 'labels']).size().unstack(fill_value=0)
    
    # Tính percentage theo từng source
    percentages = grouped.div(grouped.sum(axis=1), axis=0) * 100
    
    print("Số lượng theo nguồn và nhãn:")
    print(grouped)
    print("\nPhần trăm theo nguồn và nhãn:")
    print(percentages)
    
    sns.set_theme(style="whitegrid")
    
    # Plot Stacked Bar Chart
    ax = grouped.plot(kind='bar', stacked=True, figsize=(10, 6), color=["#2ecc71", "#e74c3c"])
    
    # Hiển thị count và percentage
    for i, container in enumerate(ax.containers):
        for j, patch in enumerate(container):
            count = int(patch.get_height())
            if count > 0:
                source_total = grouped.iloc[j].sum()
                percentage = (count / source_total) * 100
                ax.annotate(
                    f"{count:,}\n({percentage:.1f}%)",
                    (patch.get_x() + patch.get_width() / 2, patch.get_y() + patch.get_height() / 2),
                    ha='center', va='center',
                    fontsize=11, color='white', fontweight='bold'
                )
    
    plt.title("Phân bố nhãn bình luận theo nguồn dữ liệu", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Nguồn dữ liệu (Source)", fontsize=14)
    plt.ylabel("Số lượng", fontsize=14)
    plt.xticks(rotation=0)
    plt.legend(title="Nhãn (0: Bình thường, 1: Độc hại)", loc='upper right')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "label_distribution_by_source.png", dpi=300)
    plt.close()
    print("Đã lưu biểu đồ tại images/eda/label_distribution_by_source.png")

def analyze_text_length_percentiles_by_source(df):
    print("\n--- KHẢO SÁT PHÂN VỊ ĐỘ DÀI VĂN BẢN ---")
    df['word_count'] = df['comment_text'].apply(lambda x: len(str(x).split()))
    
    percentiles = [0.50, 0.75, 0.90, 0.95, 0.99]
    percentile_labels = ['P50', 'P75', 'P90', 'P95', 'P99']
    
    # Tính percentile cho Batch và Streaming
    results = {}
    for source in df['source'].unique():
        source_df = df[df['source'] == source]
        results[source] = source_df['word_count'].quantile(percentiles).values
        print(f"\nPhân vị độ dài cho {source}:")
        for p, val in zip(percentile_labels, results[source]):
            print(f"  {p}: {int(val)} từ")
            
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")
    
    markers = ['o', 's', '^', 'D']
    colors = ['#3498db', '#e67e22']
    
    for i, (source, values) in enumerate(results.items()):
        plt.plot(percentile_labels, values, marker=markers[i % len(markers)], 
                 linewidth=2, markersize=8, label=source, color=colors[i % len(colors)])
        
        # Annotate values
        for j, val in enumerate(values):
            plt.annotate(
                f"{int(val)}",
                (percentile_labels[j], val),
                textcoords="offset points",
                xytext=(0, 10),
                ha='center',
                fontsize=11,
                fontweight='bold',
                color=colors[i % len(colors)]
            )
            
    plt.title("Phân vị độ dài bình luận theo nguồn", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Phân vị (Percentile)", fontsize=14)
    plt.ylabel("Độ dài (Số lượng từ)", fontsize=14)
    plt.legend(title="Nguồn")
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "text_length_percentiles_by_source.png", dpi=300)
    plt.close()
    print("Đã lưu biểu đồ tại images/eda/text_length_percentiles_by_source.png")

def main():
    print("Đang đọc và gộp dữ liệu...")
    df1 = pd.read_csv(DATA_PATH_1)
    df1['source'] = 'Batch'
    
    # Tùy thuộc vào dữ liệu bạn có, giả sử file 2 là Streaming
    df2 = pd.read_csv(DATA_PATH_2)
    df2['source'] = 'Streaming'
    
    df = pd.concat([df1, df2], ignore_index=True)
    
    df_clean = analyze_data_quality(df)
    analyze_label_distribution_by_source(df_clean)
    analyze_text_length_percentiles_by_source(df_clean)

if __name__ == "__main__":
    main()
