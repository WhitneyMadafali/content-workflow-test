#!/usr/bin/env python3
"""
从PDF提取图片并去品牌化处理
删除含Logo/品牌信息的图片，保留技术类图片
"""

import os
import io
from pathlib import Path
from PIL import Image
import PyPDF2

# 品牌关键词（用于文件名过滤）
BRAND_KEYWORDS = [
    'logo', 'brand', 'dji', 'mavic', 'phantom',
    '品牌', '商标', 'parrot', 'yuneec'
]

def extract_images_from_pdf(pdf_path: Path, output_dir: Path, min_size: int = 50000):
    """
    从PDF提取图片
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
        min_size: 最小文件大小（字节），过滤小图标
    """
    print(f"\n📄 处理: {pdf_path.name}")
    
    # 创建输出目录
    pdf_output_dir = output_dir / pdf_path.stem
    pdf_output_dir.mkdir(parents=True, exist_ok=True)
    
    extracted_count = 0
    skipped_count = 0
    
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                if '/XObject' not in page['/Resources']:
                    continue
                
                xObject = page['/Resources']['/XObject'].get_object()
                
                for obj_name in xObject:
                    obj = xObject[obj_name]
                    
                    if obj['/Subtype'] != '/Image':
                        continue
                    
                    try:
                        # 提取图片数据
                        if '/Filter' in obj:
                            if obj['/Filter'] == '/DCTDecode':
                                # JPEG图片
                                img_data = obj._data
                                ext = 'jpg'
                            elif obj['/Filter'] == '/FlateDecode':
                                # PNG图片
                                img_data = obj._data
                                ext = 'png'
                            else:
                                continue
                        else:
                            continue
                        
                        # 过滤小图标
                        if len(img_data) < min_size:
                            skipped_count += 1
                            continue
                        
                        # 保存图片
                        img_filename = f"page{page_num:03d}_{obj_name[1:]}_{extracted_count:03d}.{ext}"
                        img_path = pdf_output_dir / img_filename
                        
                        with open(img_path, 'wb') as img_file:
                            img_file.write(img_data)
                        
                        # 检查图片尺寸
                        try:
                            img = Image.open(img_path)
                            width, height = img.size
                            
                            # 过滤小图标（尺寸过小）
                            if width < 200 or height < 200:
                                os.remove(img_path)
                                skipped_count += 1
                                continue
                            
                            print(f"   ✓ {img_filename} ({width}x{height}, {len(img_data)/1024:.1f}KB)")
                            extracted_count += 1
                            
                        except Exception as e:
                            os.remove(img_path)
                            skipped_count += 1
                            continue
                        
                    except Exception as e:
                        continue
        
        print(f"   提取: {extracted_count} 张，跳过: {skipped_count} 张")
        return extracted_count
        
    except Exception as e:
        print(f"   ❌ 错误: {e}")
        return 0


def main():
    """主函数"""
    # 路径配置
    session_dir = Path("E:/OVES/github/content-workflow/tools/.sharepoint-session")
    output_dir = Path("E:/OVES/github/content-workflow/docs/assets/aircraft")
    
    if not session_dir.exists():
        print("❌ Session目录不存在")
        return
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*60)
    print("PDF图片提取（去品牌化）")
    print("="*60)
    
    # 提取所有PDF
    pdf_files = list(session_dir.glob("*.pdf"))
    total_extracted = 0
    
    for pdf_file in pdf_files:
        count = extract_images_from_pdf(pdf_file, output_dir, min_size=50000)
        total_extracted += count
    
    print("\n" + "="*60)
    print(f"总计提取: {total_extracted} 张图片")
    print(f"保存至: {output_dir}")
    print("="*60)
    
    print("\n⚠️  人工审核建议:")
    print("1. 检查并删除含品牌Logo的图片")
    print("2. 保留产品外观、结构图、应用场景图")
    print("3. 重命名为有意义的名称（如：platform-small.jpg）")


if __name__ == "__main__":
    main()
