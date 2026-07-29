import argparse
import sys
from pathlib import Path

from prompt import MAIN_PROMPT
import os
from dotenv import load_dotenv
from google.genai import types
from google import genai
from readingFiles import read_excel
from _calculate_total import _calculate_total

load_dotenv()
FUNCTIONS = {
    'read_excel': read_excel,
    'calculate_total': _calculate_total,
}

TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name='read_excel',
            description='Read .xls/.xlsx/.csv/.html files (single file or directory), detect the actual content type from binary signatures, and return the extracted data as a list of dicts',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'file_path': types.Schema(type=types.Type.STRING, description='Path to the file or directory'),
                },
                required=['file_path']
            ),
        ),
        types.FunctionDeclaration(
            name='calculate_total',
            description='Receive a list of extracted data dicts, sanitize them, and calculate the total sum of PRECIO * CANTIDAD for each row',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'data': types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                'PRECIO': types.Schema(type=types.Type.STRING, description='Price of the product'),
                                'CANTIDAD': types.Schema(type=types.Type.STRING, description='Quantity of the product'),
                            },
                        ),
                        description='List of extracted data rows with PRECIO and CANTIDAD fields',
                    ),
                },
                required=['data']
            ),
        ),
    ])
]


def debug_data(data: list[dict], label: str = "Data collected") -> None:
    print(f"\n--- {label} ---")
    if not data:
        print("(empty)")
    else:
        print(f"Rows: {len(data)}")
        for i, row in enumerate(data):
            print(f"  [{i}] {dict(row)}")
    print("--------------------\n")

def get_client() -> genai.Client:
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise ValueError('Gemini API key required. Set GEMINI_API_KEY env var.')
    return genai.Client(api_key=key)


def main(file_path: str) -> float:
    client = get_client()
    contents = [
        types.Content(
            role='user',
            parts=[types.Part.from_text(text=MAIN_PROMPT + f"\n\nRead the Excel file or directory at: {file_path}")]
        )
    ]

    total = None

    for turn in range(5):
        response = client.models.generate_content(
            model='gemini-3.1-flash-lite',
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        if not response.candidates:
            break

        parts = response.candidates[0].content.parts
        function_calls = [p.function_call for p in parts if p.function_call]

        if function_calls:
            fn = function_calls[0]
            contents.append(response.candidates[0].content)
            result = FUNCTIONS[fn.name](**{k: v for k, v in fn.args.items()})

            if fn.name == 'read_excel':
                debug_data(result, "Data collected by the model")

            if fn.name == 'calculate_total':
                total = result

            contents.append(types.Content(
                role='tool',
                parts=[types.Part.from_function_response(
                    name=fn.name,
                    response={'result': result},
                )]
            ))
        else:
            for part in parts:
                if part.text:
                    print(part.text)
            break

    return total


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Calculate IVA total from an Excel file or directory.'
    )
    parser.add_argument(
        'file_path',
        help='Path to the Excel file or directory'
    )
    args = parser.parse_args()

    if not Path(args.file_path).exists():
        print(f"Error: The path '{args.file_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    total = main(args.file_path)
    if total is not None:
        print(total)
