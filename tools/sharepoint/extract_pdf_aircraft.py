#!/usr/bin/env python3
"""
提取PDF内容并去品牌化处理
提取技术参数、性能指标，删除厂家Logo/品牌信息
"""

import json
import re
from pathlib import Path
from typing import Dict, List
from datetime import datetime

try:
    import PyPDF2
    from PIL import Image
    import io
except ImportError:
    print("❌ 缺少依赖包")
    print("\n安装命令:")
    print("  pip install PyPDF2 Pillow")
    exit(1)


class PDFExtractor:
    """PDF内容提取器（去品牌化）"""
    
    # 需要删除的品牌关键词
    BRAND_KEYWORDS = [
        'DJI', '大疆', 'Mavic', 'Phantom', 'Inspire',
        'Parrot', 'Yuneec', 'Autel', 'Skydio',
        '极飞', 'XAG', '亿航', 'EHang'
    ]
    
    # 技术参数关键词
    TECH_KEYWORDS = [
        '续航', '载重', '飞行时间', '最大速度', '航程',
        '电池容量', '充电时间', '遥控距离', '图传距离',
        '抗风等级', '工作温度', '精度', '分辨率',
        '尺寸', '重量', 'GPS', '传感器', '避障'
    ]
    
    def __init__(self, session_dir: Path):
        self.session_dir = session_dir
        self.results = {
            "extraction_date": datetime.now().isoformat(),
            "files": []
        }
    
    def is_brand_content(self, text: str) -> bool:
        """检查是否包含品牌信息"""
        text_lower = text.lower()
        for keyword in self.BRAND_KEYWORDS:
            if keyword.lower() in text_lower:
                return True
        return False
    
    def extract_tech_params(self, text: str) -> List[str]:
        """提取技术参数"""
        params = []
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 跳过品牌内容
            if self.is_brand_content(line):
                continue
            
            # 检查是否包含技术关键词
            for keyword in self.TECH_KEYWORDS:
                if keyword in line:
                    # 提取包含数字和单位的参数
                    if re.search(r'\d+', line):
                        params.append(line)
                    break
        
        return params
    
    def extract_pdf(self, pdf_path: Path) -> Dict:
        """提取单个PDF文件"""
        print(f"\n📄 处理: {pdf_path.name}")
        
        result = {
            "file_name": pdf_path.name,
            "file_size": pdf_path.stat().st_size,
            "total_pages": 0,
            "tech_params": [],
            "clean_text": [],
            "has_images": False,
            "image_count": 0
        }
        
        try:
            with open(pdf_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                result["total_pages"] = len(pdf_reader.pages)
                
                print(f"   页数: {result['total_pages']}")
                
                # 提取文本
                all_text = []
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    text = page.extract_text()
                    if text:
                        all_text.append(text)
                
                # 合并文本
                full_text = '\n'.join(all_text)
                
                # 提取技术参数
                result["tech_params"] = self.extract_tech_params(full_text)
                
                # 清理文本（删除品牌信息）
                clean_lines = []
                for line in full_text.split('\n'):
                    line = line.strip()
                    if line and not self.is_brand_content(line):
                        # 保留有价值的行（包含中文或数字）
                        if re.search(r'[\u4e00-\u9fff]', line) or re.search(r'\d', line):
                            clean_lines.append(line)
                
                result["clean_text"] = clean_lines[:100]  # 前100行
                
                # 检查图片
                for page in pdf_reader.pages:
                    if '/XObject' in page['/Resources']:
                        xObject = page['/Resources']['/XObject'].get_object()
                        for obj in xObject:
                            if xObject[obj]['/Subtype'] == '/Image':
                                result["has_images"] = True
                                result["image_count"] += 1
                
                print(f"   技术参数: {len(result['tech_params'])} 条")
                print(f"   清洁文本: {len(result['clean_text'])} 行")
                print(f"   图片数: {result['image_count']} 张")
                
        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ 错误: {e}")
        
        return result
    
    def extract_all(self) -> Dict:
        """提取所有PDF文件"""
        print("\n" + "="*60)
        print("PDF内容提取（去品牌化）")
        print("="*60)
        
        pdf_files = list(self.session_dir.glob("*.pdf"))
        
        if not pdf_files:
            print("\n❌ 未找到PDF文件")
            return self.results
        
        print(f"\n找到 {len(pdf_files)} 个PDF文件")
        
        for pdf_file in pdf_files:
            result = self.extract_pdf(pdf_file)
            self.results["files"].append(result)
        
        return self.results
    
    def generate_comparison_data(self) -> Dict:
        """生成市场对比数据（基于提取的参数）"""
        print("\n" + "="*60)
        print("生成市场对比数据")
        print("="*60)
        
        comparison = {
            "generation_date": datetime.now().isoformat(),
            "categories": []
        }
        
        # 按文件分类
        for file_data in self.results["files"]:
            if "error" in file_data:
                continue
            
            category = {
                "source_file": file_data["file_name"],
                "extracted_specs": [],
                "market_position": "参考行业平均水平",
                "competitive_advantages": []
            }
            
            # 整理技术参数
            for param in file_data["tech_params"][:20]:  # 前20条
                # 提取数值
                numbers = re.findall(r'\d+\.?\d*', param)
                if numbers:
                    category["extracted_specs"].append({
                        "parameter": param,
                        "value": numbers[0] if numbers else "N/A"
                    })
            
            comparison["categories"].append(category)
        
        return comparison


def main():
    """主函数"""
    # Session目录
    session_dir = Path("E:/OVES/github/content-workflow/tools/.sharepoint-session")
    
    if not session_dir.exists():
        print("❌ Session目录不存在")
        return
    
    # 提取PDF
    extractor = PDFExtractor(session_dir)
    results = extractor.extract_all()
    
    # 保存提取结果
    output_file = Path(__file__).parent / "aircraft-extracted.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ 提取结果保存至: {output_file}")
    
    # 生成对比数据
    comparison = extractor.generate_comparison_data()
    comparison_file = Path(__file__).parent / "aircraft-comparison.json"
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 对比数据保存至: {comparison_file}")
    
    # 显示摘要
    print("\n" + "="*60)
    print("提取摘要")
    print("="*60)
    for file_data in results["files"]:
        print(f"\n📄 {file_data['file_name']}")
        print(f"   页数: {file_data['total_pages']}")
        print(f"   技术参数: {file_data.get('tech_params', [])[:3]}")


if __name__ == "__main__":
    main()
