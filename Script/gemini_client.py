import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from readingFiles import read_excel
from creatingFile import create_excel
from writingFiles import write_excel

load_dotenv()

FUNCTIONS = {
    'read_excel': read_excel,
    'create_excel': create_excel,
    'write_excel': write_excel,
}

TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name='read_excel',
            description='Read raw binary of .xls/.xlsx files (single file or directory), detect the actual content type from binary signatures (xls, xlsx, html, csv, unknown), and return each base64-encoded with detected_type for conversion code generation.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'file_path': types.Schema(type=types.Type.STRING, description='Path to the Excel file.'),
                },
                required=['file_path'],
            ),
        ),
        types.FunctionDeclaration(
            name='create_excel',
            description='Create an .xls file with timestamped filename [NAME_DDMMYY].xls. Structure: row 0 blank, row 1 headers [EAN, NOMBRE, PRECIO, (empty), CANTIDAD], data from row 2.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'name': types.Schema(type=types.Type.STRING, description='Company name for the file'),
                    'data': types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                'EAN': types.Schema(type=types.Type.STRING),
                                'NOMBRE': types.Schema(type=types.Type.STRING),
                                'PRECIO': types.Schema(type=types.Type.STRING),
                                'CANTIDAD': types.Schema(type=types.Type.STRING),
                                'VACIO': types.Schema(type=types.Type.STRING),
                            },
                        ),
                        description='Rows as dicts with keys EAN, NOMBRE, PRECIO, CANTIDAD.',
                    ),
                },
                required=['name', 'data'],
            ),
        ),
        types.FunctionDeclaration(
            name='write_excel',
            description='Append rows to an existing .xls file, preserving the existing structure.',
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    'file_path': types.Schema(type=types.Type.STRING, description='Path to the existing .xls file.'),
                    'data': types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                'EAN': types.Schema(type=types.Type.STRING),
                                'NOMBRE': types.Schema(type=types.Type.STRING),
                                'PRECIO': types.Schema(type=types.Type.STRING),
                                'CANTIDAD': types.Schema(type=types.Type.STRING),
                                'VACIO': types.Schema(type=types.Type.STRING),
                            },
                        ),
                        description='Rows as dicts with keys EAN, NOMBRE, PRECIO, CANTIDAD.',
                    ),
                },
                required=['file_path', 'data'],
            ),
        ),
    ])
]


def get_client() -> genai.Client:
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        raise ValueError('Gemini API key required. Set GEMINI_API_KEY env var.')
    return genai.Client(api_key=key)


def generate_with_tools(prompt: str, model: str = 'gemini-3.1-flash-lite', max_turns: int = 10) -> str:
    c = get_client()
    contents = [types.Content(role='user', parts=[types.Part.from_text(text=prompt)])]

    for turn in range(max_turns):
        print(f'\n--- Turn {turn + 1} ---')
        response = c.models.generate_content(
            model=model,
            contents=contents,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        if not response.candidates or not response.candidates[0].content.parts:
            raise RuntimeError("Empty response from model.")

        parts = response.candidates[0].content.parts
        function_calls = [p.function_call for p in parts if p.function_call]

        if function_calls:
            fn = function_calls[0]
            contents.append(response.candidates[0].content)

            print(f'Calling: {fn.name}({dict(fn.args.items())})')
            result = FUNCTIONS[fn.name](**{k: v for k, v in fn.args.items()})
            print(f'Result: {result}')

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
                    return part.text

    raise RuntimeError('Max turns reached without final response')
