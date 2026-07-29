import sys
from pathlib import Path

from prompt import MAIN_PROMPT

from google.genai import types
from readingFiles import read_excel
from calculateIVA import _calculate_total
from gemini_client import get_client


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

    print(f"Total: {total:.2f}" if total is not None else "Total: N/A")
    return total


if __name__ == '__main__':
    file_path: str = input('Enter the path to the Excel file or directory: ').strip()
    if not Path(file_path).exists():
        print(f"Error: The path '{file_path}' does not exist.")
        sys.exit(1)
    main(file_path)
