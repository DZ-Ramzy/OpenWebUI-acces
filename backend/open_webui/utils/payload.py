from open_webui.utils.task import prompt_template, prompt_variables_template
from open_webui.utils.misc import (
    add_or_update_system_message,
)

from typing import Callable, Optional
import json


# inplace function: form_data is modified
def apply_model_system_prompt_to_body(
    params: dict, form_data: dict, metadata: Optional[dict] = None, user=None
) -> dict:
    system = params.get("system", None)
    if not system:
        return form_data

    # Check for Easy Read mode in metadata
    easyread_mode = metadata.get("easyread-mode", False) if metadata else False
    easyread_language = metadata.get("easyread-language", "fr") if metadata else "fr"
    
    # Add Easy Read instruction if enabled
    if easyread_mode:
        easyread_instructions = {
            "fr": """Tu dois répondre en français facile à lire et à comprendre (FALC). Suis ces règles strictement :
                1.Utilise uniquement des mots simples et du quotidien
                2.Écris des phrases très courtes (maximum 10 à 15 mots)
                3.Évite tous les termes techniques et le jargon
                4.Utilise la voix active (et non la forme passive)
                5.Découpe les idées complexes en étapes simples
                6.Utilise des listes à puces ou des listes numérotées si possible
                7.Ajoute des transitions claires entre les idées
                8.Répète les informations importantes
                9.Utilise des exemples pour expliquer les concepts difficiles""",
            "en": """You must answer in Easy-to-Read English. Follow these rules strictly:
                1. Use only simple, everyday words
                2. Write very short sentences (maximum 10-15 words)
                3. Avoid all technical terms and jargon
                4. Use active voice instead of passive
                5. Break down complex ideas into simple steps
                6. Use bullet points or numbered lists when possible
                7. Add clear transitions between ideas
                8. Repeat important information
                9. Use examples to explain difficult concepts""",
            "es": """Debes responder en Español Fácil de Leer y Comprender. Sigue estas reglas estrictamente:
                1. Usa solo palabras simples y cotidianas
                2. Escribe oraciones muy cortas (máximo 10-15 palabras)
                3. Evita todos los términos técnicos y jerga
                4. Usa voz activa en lugar de pasiva
                5. Divide ideas complejas en pasos simples
                6. Usa viñetas o listas numeradas cuando sea posible
                7. Agrega transiciones claras entre ideas
                8. Repite información importante
                9. Usa ejemplos para explicar conceptos difíciles""",
            "de": """Sie müssen in Einfacher Sprache antworten. Folgen Sie diesen Regeln strikt:
                1. Verwenden Sie nur einfache, alltägliche Wörter
                2. Schreiben Sie sehr kurze Sätze (maximal 10-15 Wörter)
                3. Vermeiden Sie alle Fachbegriffe und Jargon
                4. Verwenden Sie aktive statt passive Stimme
                5. Teilen Sie komplexe Ideen in einfache Schritte auf
                6. Verwenden Sie Aufzählungszeichen oder nummerierte Listen wenn möglich
                7. Fügen Sie klare Übergänge zwischen Ideen hinzu
                8. Wiederholen Sie wichtige Informationen
                9. Verwenden Sie Beispiele um schwierige Konzepte zu erklären""",
            "it": """Devi rispondere in Italiano Semplice da Leggere e Comprendere. Segui queste regole rigorosamente:
                1. Usa solo parole semplici e quotidiane
                2. Scrivi frasi molto brevi (massimo 10-15 parole)
                3. Evita tutti i termini tecnici e il gergo
                4. Usa la voce attiva invece di quella passiva
                5. Suddividi idee complesse in passi semplici
                6. Usa elenchi puntati o numerati quando possibile
                7. Aggiungi transizioni chiare tra le idee
                8. Ripeti le informazioni importanti
                9. Usa esempi per spiegare concetti difficili""",
            "ar": """يجب أن تجيب باللغة العربية المبسطة. اتبع هذه القواعد بدقة:
                1. استخدم كلمات بسيطة ومألوفة فقط
                2. اكتب جمل قصيرة جداً (10-15 كلمة كحد أقصى)
                3. تجنب جميع المصطلحات التقنية والمصطلحات المتخصصة
                4. استخدم الصيغة الفعلية بدلاً من الصيغة المجهولة
                5. قسم الأفكار المعقدة إلى خطوات بسيطة
                6. استخدم النقاط أو القوائم المرقمة عندما يكون ذلك ممكناً
                7. أضف انتقالات واضحة بين الأفكار
                8. كرر المعلومات المهمة
                9. استخدم أمثلة لشرح المفاهيم الصعبة"""
        }
        easyread_instruction = easyread_instructions.get(easyread_language, easyread_instructions["fr"])
        system = f"{easyread_instruction}\n\n{system}"

    # Metadata (WebUI Usage)
    if metadata:
        variables = metadata.get("variables", {})
        if variables:
            system = prompt_variables_template(system, variables)

    # Legacy (API Usage)
    if user:
        template_params = {
            "user_name": user.name,
            "user_location": user.info.get("location") if user.info else None,
        }
    else:
        template_params = {}

    system = prompt_template(system, **template_params)

    form_data["messages"] = add_or_update_system_message(
        system, form_data.get("messages", [])
    )
    return form_data


# inplace function: form_data is modified
def apply_model_params_to_body(
    params: dict, form_data: dict, mappings: dict[str, Callable]
) -> dict:
    if not params:
        return form_data

    for key, cast_func in mappings.items():
        if (value := params.get(key)) is not None:
            form_data[key] = cast_func(value)

    return form_data


# inplace function: form_data is modified
def apply_model_params_to_body_openai(params: dict, form_data: dict) -> dict:
    mappings = {
        "temperature": float,
        "top_p": float,
        "max_tokens": int,
        "frequency_penalty": float,
        "reasoning_effort": str,
        "seed": lambda x: x,
        "stop": lambda x: [bytes(s, "utf-8").decode("unicode_escape") for s in x],
        "logit_bias": lambda x: x,
        "response_format": dict,
    }
    return apply_model_params_to_body(params, form_data, mappings)


def apply_model_params_to_body_ollama(params: dict, form_data: dict) -> dict:
    # Convert OpenAI parameter names to Ollama parameter names if needed.
    name_differences = {
        "max_tokens": "num_predict",
    }

    for key, value in name_differences.items():
        if (param := params.get(key, None)) is not None:
            # Copy the parameter to new name then delete it, to prevent Ollama warning of invalid option provided
            params[value] = params[key]
            del params[key]

    # See https://github.com/ollama/ollama/blob/main/docs/api.md#request-8
    mappings = {
        "temperature": float,
        "top_p": float,
        "seed": lambda x: x,
        "mirostat": int,
        "mirostat_eta": float,
        "mirostat_tau": float,
        "num_ctx": int,
        "num_batch": int,
        "num_keep": int,
        "num_predict": int,
        "repeat_last_n": int,
        "top_k": int,
        "min_p": float,
        "typical_p": float,
        "repeat_penalty": float,
        "presence_penalty": float,
        "frequency_penalty": float,
        "penalize_newline": bool,
        "stop": lambda x: [bytes(s, "utf-8").decode("unicode_escape") for s in x],
        "numa": bool,
        "num_gpu": int,
        "main_gpu": int,
        "low_vram": bool,
        "vocab_only": bool,
        "use_mmap": bool,
        "use_mlock": bool,
        "num_thread": int,
    }

    # Extract keep_alive from options if it exists
    if "options" in form_data and "keep_alive" in form_data["options"]:
        form_data["keep_alive"] = form_data["options"]["keep_alive"]
        del form_data["options"]["keep_alive"]

    if "options" in form_data and "format" in form_data["options"]:
        form_data["format"] = form_data["options"]["format"]
        del form_data["options"]["format"]

    return apply_model_params_to_body(params, form_data, mappings)


def convert_messages_openai_to_ollama(messages: list[dict]) -> list[dict]:
    ollama_messages = []

    for message in messages:
        # Initialize the new message structure with the role
        new_message = {"role": message["role"]}

        content = message.get("content", [])
        tool_calls = message.get("tool_calls", None)
        tool_call_id = message.get("tool_call_id", None)

        # Check if the content is a string (just a simple message)
        if isinstance(content, str) and not tool_calls:
            # If the content is a string, it's pure text
            new_message["content"] = content

            # If message is a tool call, add the tool call id to the message
            if tool_call_id:
                new_message["tool_call_id"] = tool_call_id

        elif tool_calls:
            # If tool calls are present, add them to the message
            ollama_tool_calls = []
            for tool_call in tool_calls:
                ollama_tool_call = {
                    "index": tool_call.get("index", 0),
                    "id": tool_call.get("id", None),
                    "function": {
                        "name": tool_call.get("function", {}).get("name", ""),
                        "arguments": json.loads(
                            tool_call.get("function", {}).get("arguments", {})
                        ),
                    },
                }
                ollama_tool_calls.append(ollama_tool_call)
            new_message["tool_calls"] = ollama_tool_calls

            # Put the content to empty string (Ollama requires an empty string for tool calls)
            new_message["content"] = ""

        else:
            # Otherwise, assume the content is a list of dicts, e.g., text followed by an image URL
            content_text = ""
            images = []

            # Iterate through the list of content items
            for item in content:
                # Check if it's a text type
                if item.get("type") == "text":
                    content_text += item.get("text", "")

                # Check if it's an image URL type
                elif item.get("type") == "image_url":
                    img_url = item.get("image_url", {}).get("url", "")
                    if img_url:
                        # If the image url starts with data:, it's a base64 image and should be trimmed
                        if img_url.startswith("data:"):
                            img_url = img_url.split(",")[-1]
                        images.append(img_url)

            # Add content text (if any)
            if content_text:
                new_message["content"] = content_text.strip()

            # Add images (if any)
            if images:
                new_message["images"] = images

        # Append the new formatted message to the result
        ollama_messages.append(new_message)

    return ollama_messages


def convert_payload_openai_to_ollama(openai_payload: dict) -> dict:
    """
    Converts a payload formatted for OpenAI's API to be compatible with Ollama's API endpoint for chat completions.

    Args:
        openai_payload (dict): The payload originally designed for OpenAI API usage.

    Returns:
        dict: A modified payload compatible with the Ollama API.
    """
    ollama_payload = {}

    # Mapping basic model and message details
    ollama_payload["model"] = openai_payload.get("model")
    ollama_payload["messages"] = convert_messages_openai_to_ollama(
        openai_payload.get("messages")
    )
    ollama_payload["stream"] = openai_payload.get("stream", False)

    if "tools" in openai_payload:
        ollama_payload["tools"] = openai_payload["tools"]

    if "format" in openai_payload:
        ollama_payload["format"] = openai_payload["format"]

    # If there are advanced parameters in the payload, format them in Ollama's options field
    if openai_payload.get("options"):
        ollama_payload["options"] = openai_payload["options"]
        ollama_options = openai_payload["options"]

        # Re-Mapping OpenAI's `max_tokens` -> Ollama's `num_predict`
        if "max_tokens" in ollama_options:
            ollama_options["num_predict"] = ollama_options["max_tokens"]
            del ollama_options[
                "max_tokens"
            ]  # To prevent Ollama warning of invalid option provided

        # Ollama lacks a "system" prompt option. It has to be provided as a direct parameter, so we copy it down.
        if "system" in ollama_options:
            ollama_payload["system"] = ollama_options["system"]
            del ollama_options[
                "system"
            ]  # To prevent Ollama warning of invalid option provided

        # Extract keep_alive from options if it exists
        if "keep_alive" in ollama_options:
            ollama_payload["keep_alive"] = ollama_options["keep_alive"]
            del ollama_options["keep_alive"]

    # If there is the "stop" parameter in the openai_payload, remap it to the ollama_payload.options
    if "stop" in openai_payload:
        ollama_options = ollama_payload.get("options", {})
        ollama_options["stop"] = openai_payload.get("stop")
        ollama_payload["options"] = ollama_options

    if "metadata" in openai_payload:
        ollama_payload["metadata"] = openai_payload["metadata"]

    if "response_format" in openai_payload:
        response_format = openai_payload["response_format"]
        format_type = response_format.get("type", None)

        schema = response_format.get(format_type, None)
        if schema:
            format = schema.get("schema", None)
            ollama_payload["format"] = format

    return ollama_payload
