import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Cấu hình đường dẫn thư mục
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH_1 = PROJECT_ROOT / "data_local" / "raw" / "text_comment_1.csv"
DATA_PATH_2 = PROJECT_ROOT / "data_local" / "raw" / "text_comment_2.csv"
OUTPUT_IMG = PROJECT_ROOT / "images" / "label_distribution.png"

def main():
    print("Reading datasets...")
    df1 = pd.read_csv(DATA_PATH_1)
    df2 = pd.read_csv(DATA_PATH_2)
    df = pd.concat([df1, df2], ignore_index=True)
    
    # Tính toán số lượng và phần trăm
    total_samples = len(df)
    counts = df['labels'].value_counts().sort_index()
    percentages = (counts / total_samples) * 100
    
    print(f"Tổng số mẫu: {total_samples}")
    print(f"Nhãn 0 (Không độc hại): {counts[0]} ({percentages[0]:.2f}%)")
    print(f"Nhãn 1 (Độc hại): {counts[1]} ({percentages[1]:.2f}%)")
    
    # Thiết lập style đồ thị
    sns.set_theme(style="whitegrid")
    plt.figure(figsize=(8, 6))
    
    # Vẽ biểu đồ cột
    ax = sns.barplot(
        x=["Không độc hại (0)", "Độc hại (1)"], 
        y=counts.values, 
        palette=["#2ecc71", "#e74c3c"]
    )
    
    # Thêm số liệu lên trên từng cột
    for i, p in enumerate(ax.patches):
        ax.annotate(
            f"{int(p.get_height()):,}\n({percentages[i]:.2f}%)", 
            (p.get_x() + p.get_width() / 2., p.get_height()), 
            ha='center', va='bottom', 
            fontsize=12, fontweight='bold', color='black', xytext=(0, 5), 
            textcoords='offset points'
        )
        
    plt.title("Phân bố nhãn của bộ dữ liệu bình luận", fontsize=16, fontweight='bold', pad=20)
    plt.xlabel("Phân loại nhãn", fontsize=14, labelpad=10)
    plt.ylabel("Số lượng mẫu", fontsize=14, labelpad=10)
    
    # Chỉnh lại khoảng hiển thị trục Y để text không bị cắt
    plt.ylim(0, max(counts.values) * 1.15)
    
    # Lưu và hiển thị
    OUTPUT_IMG.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMG, dpi=300)
    print(f"Đã lưu biểu đồ tại: {OUTPUT_IMG}")
    
if __name__ == "__main__":
    main()
