#!/usr/bin/env python3
"""WeRead One-Click Book Exporter (main.py)

一键无损抓取并导出微信读书全格式电子书（PDF / EPUB / Markdown）

用法:
    python main.py <微信读书网页链接或书籍ID>

示例:
    python main.py https://weread.qq.com/web/reader/3b132980813ab94eeg013129
    python main.py 3b132980813ab94eeg013129
"""
import argparse
import asyncio
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import crawl_weread
import export_book


def print_banner():
    print("""
===========================================================
  📚 WeRead Book Exporter - 微信读书全书无损一键导出工具
===========================================================
    """)


async def run(raw_input, force=False, last=None, chapter_from=None, chapter_to=None):
    book_id = crawl_weread.extract_book_id(raw_input)
    if not book_id:
        print("❌ 错误: 请输入有效的微信读书网页链接或书籍 ID！")
        print("👉 示例: python main.py https://weread.qq.com/web/reader/3b132980813ab94eeg013129")
        sys.exit(1)

    selective = last is not None or chapter_from is not None or chapter_to is not None
    dir_suffix = crawl_weread.selection_dir_suffix(last, chapter_from, chapter_to) if selective else "_v2"
    out_tag = "（节选）" if selective else ""

    print(f"🚀 开始执行一键全流程导出，书籍 ID: {book_id}\n")
    if selective:
        scope = f"最后 {last} 章" if last is not None else f"{chapter_from or '开头'} → {chapter_to or '结尾'}"
        print(f"🎯 本次仅抓取指定章节范围: {scope}\n")
        print("【步骤 1/2】抓取指定章节、插图与原版封面...")
    else:
        print("【步骤 1/2】抓取全书章节、插图与原版封面...")
    crawl_ok = await crawl_weread.main(
        book_id, force=force, last=last,
        chapter_from=chapter_from, chapter_to=chapter_to,
        dir_suffix=dir_suffix,
    )
    if not crawl_ok:
        print("\n❌ 抓取未完成，导出终止。请检查网络或重新扫码。")
        sys.exit(1)

    # 第二步：一键多格式导出
    print("\n【步骤 2/2】正在生成精排 PDF、EPUB 与 Markdown 笔记...")
    export_ok = await export_book.main(book_id, dir_suffix=dir_suffix, out_tag=out_tag)
    if not export_ok:
        print("\n❌ 导出过程遇到错误，请检查日志。")
        sys.exit(1)

    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "output"))
    print("=" * 60)
    print(f"🎉 全部完成！导出的所有文件已保存在:\n👉 {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    print_banner()

    parser = argparse.ArgumentParser(description="微信读书全书/指定章节无损导出")
    parser.add_argument("book", nargs="?", help="微信读书网页链接或书籍 ID")
    parser.add_argument("-f", "--force", action="store_true", help="强制重新完整抓取")
    parser.add_argument("--last", type=int, metavar="N", help="仅抓取目录最后 N 章")
    parser.add_argument("--from", dest="chapter_from", metavar="章节",
                        help="起始章节（目录序号从 1 开始，或标题关键字）")
    parser.add_argument("--to", dest="chapter_to", metavar="章节",
                        help="结束章节（目录序号从 1 开始，或标题关键字）")
    args = parser.parse_args()

    if args.last is not None and (args.chapter_from is not None or args.chapter_to is not None):
        parser.error("--last 不能与 --from/--to 同时使用")

    if not args.book:
        try:
            user_input = input("请输入微信读书网页链接或书籍 ID: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n已取消。")
            sys.exit(0)
        if not user_input:
            print("未输入有效链接或 ID，程序退出。")
            sys.exit(0)
    else:
        user_input = args.book.strip()

    asyncio.run(run(
        user_input, force=args.force, last=args.last,
        chapter_from=args.chapter_from, chapter_to=args.chapter_to,
    ))
