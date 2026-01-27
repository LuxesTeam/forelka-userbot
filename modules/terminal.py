import sys
import asyncio
from pyrogram.enums import ParseMode

async def term_cmd(client, message, args):
    pref = getattr(client, "prefix", ".")
    if not args:
        return await message.edit(
            f"<emoji id=5877468380125990242>➡️</emoji> <b>Terminal</b>\n"
            f"<code>{pref}term &lt;command&gt;</code>",
            parse_mode=ParseMode.HTML
        )

    cmd = " ".join(args)

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await proc.communicate()
    out = (stdout or b"").decode(errors="ignore").strip()
    err = (stderr or b"").decode(errors="ignore").strip()

    text = f"<b>$</b> <code>{cmd}</code>\n\n"

    if out:
        text += f"<b>stdout:</b>\n<blockquote expandable><code>{out}</code></blockquote>\n\n"
    if err:
        text += f"<b>stderr:</b>\n<blockquote expandable><code>{err}</code></blockquote>\n\n"

    text += f"<b>exit code:</b> <code>{proc.returncode}</code>"

    if len(text) > 4000:
        cut = 4000 - len("</code></blockquote>")
        text = text[:cut] + "</code></blockquote>"

    await message.edit(text, parse_mode=ParseMode.HTML)

async def eval_cmd(client, message, args):
    """Выполнить Python код"""
    if not args:
        return await message.edit(
            "<emoji id=5877468380125990242>➡️</emoji> <b>Evaluator</b>\n"
            f"<code>{getattr(client, 'prefix', '.')}eval &lt;code&gt;</code>",
            parse_mode=ParseMode.HTML
        )

    code = " ".join(args)

    # Подготовим окружение для выполнения кода
    env = {
        'client': client,
        'message': message,
        'args': args,
        'reply': message.reply_to_message,
        'print': lambda *a: a,
        '__builtins__': __builtins__,
        'asyncio': asyncio,
        'event': message  # Для совместимости с некоторыми скриптами
    }

    try:
        # Попробуем выполнить как выражение (return)
        try:
            result = eval(code, env)
            if asyncio.iscoroutine(result):
                result = await result
            output = str(result)
        except SyntaxError:
            # Если это не выражение, выполним как блок кода
            # Создаем асинхронную функцию для выполнения кода
            exec_code = f"async def __temp_async_func(client, message):\n"
            for line in code.split('\n'):
                exec_code += f"    {line}\n"

            # Выполняем код, чтобы создать функцию
            exec(exec_code, env)
            # Вызываем созданную функцию
            result = env['__temp_async_func'](client, message)
            # Если результат - корутина, ждем её
            if asyncio.iscoroutine(result):
                result = await result
            output = str(result) if result is not None else "None"

        text = f"<b>🐍 Eval:</b> <code>{code}</code>\n\n"
        text += f"<b>📤 Result:</b>\n<blockquote expandable><code>{output}</code></blockquote>"

        if len(text) > 4000:
            cut = 4000 - len("</code></blockquote>")
            text = text[:cut] + "</code></blockquote>"

        await message.edit(text, parse_mode=ParseMode.HTML)

    except Exception as e:
        error_text = f"<b>🐍 Eval:</b> <code>{code}</code>\n\n"
        error_text += f"<b>❌ Error:</b>\n<blockquote expandable><code>{type(e).__name__}: {str(e)}</code></blockquote>"

        if len(error_text) > 4000:
            cut = 4000 - len("</code></blockquote>")
            error_text = error_text[:cut] + "</code></blockquote>"

        await message.edit(error_text, parse_mode=ParseMode.HTML)

def register(app, commands, module_name):
    commands["term"] = {"func": term_cmd, "module": module_name}
    commands["eval"] = {"func": eval_cmd, "module": module_name}
