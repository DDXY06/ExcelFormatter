from gemini_client import generate_with_tools
from prompts import MAIN_PROMPT


def main() -> None:
    source = input('Source file path: ').strip()
    name = input('Company name: ').strip()
    prompt = f'{MAIN_PROMPT}\n\nSource file/directory: {source}\nCompany name: {name}'
    result = generate_with_tools(prompt)
    print(result)


if __name__ == '__main__':
    main()
