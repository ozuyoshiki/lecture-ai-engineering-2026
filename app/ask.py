"""第1回: 会話履歴を保ちながら、素のLLMに質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask            # 質問を省略すると、講座に固有の質問をする

最初の質問への回答後も、会話履歴を引き継いで続けて質問できる。
終了するには exit、quit、q のいずれかを入力する。
ツールを持たない「素の」呼び出し。
講座に固有のことを聞くと、「分からない」と答えるか、一般論でもっともらしく答える
（講座の実際とは違う）ことを確かめよう。
（第3回で、用語集を検索できるエージェントにして改善する）
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def print_response(response: genai.types.GenerateContentResponse) -> None:
    usage = response.usage_metadata
    input_tokens = usage.prompt_token_count if usage is not None else None
    output_tokens = usage.candidates_token_count if usage is not None else None
    input_display = input_tokens if input_tokens is not None else "不明"
    output_display = output_tokens if output_tokens is not None else "不明"
    print(f"[トークン数] 入力: {input_display}, 出力: {output_display}")
    print(response.text)


def main() -> None:
    parser = argparse.ArgumentParser(description="素のLLMに質問する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    try:
        client = genai.Client(api_key=get_api_key())
        chat = client.chats.create(model=MODEL)
        question = args.question

        print(f"[model] {MODEL}", flush=True)
        while True:
            print(f"[質問] {question}", flush=True)
            response = chat.send_message(question)
            print_response(response)

            try:
                question = input("\n続けて質問できます（終了: exit / quit / q）\n> ").strip()
            except EOFError:
                break
            if question.lower() in {"exit", "quit", "q"}:
                break
            if not question:
                continue
    except errors.APIError as e:
        print(api_error_message(e.code, e.message))
        raise SystemExit(1)
    except KeyboardInterrupt:
        print("\n[終了] Ctrl+C で中断しました。")


if __name__ == "__main__":
    main()
