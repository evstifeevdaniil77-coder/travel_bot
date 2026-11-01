import html
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import aiofiles
from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import settings
from states import QUESTIONS, TravelCustDev

router = Router()
DATA_FILE = Path("data/responses.json")


async def save_response_to_file(record: dict) -> None:
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    responses = []

    if DATA_FILE.exists():
        try:
            async with aiofiles.open(DATA_FILE, mode="r", encoding="utf-8") as f:
                content = await f.read()
                if content.strip():
                    responses = json.loads(content)
        except Exception as exc:
            logging.error(f"Failed to read existing responses file: {exc}")

    responses.append(record)

    async with aiofiles.open(DATA_FILE, mode="w", encoding="utf-8") as f:
        await f.write(json.dumps(responses, ensure_ascii=False, indent=2))


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    welcome_text = (
        "👋 <b>Привет!</b>\n\n"
        "Мы проводим исследование опыта путешественников, чтобы создать сервис, "
        "который избавит от главных болей и стресса в поездках.\n\n"
        "Опрос состоит из <b>7 коротких вопросов</b> и займет 2–3 минуты. "
        "В любой момент вы можете отменить опрос командой /cancel.\n\n"
        f"<b>Вопрос 1 из 7:</b>\n{QUESTIONS['step_location']}"
    )
    await state.set_state(TravelCustDev.step_location)
    await message.answer(welcome_text, parse_mode=ParseMode.HTML)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Сейчас нет активного опроса. Нажмите /start, чтобы начать.")
        return

    await state.clear()
    await message.answer(
        "❌ Опрос отменен. Если захотите пройти его заново, нажмите /start."
    )


@router.message(TravelCustDev.step_location, F.text)
async def process_location(message: Message, state: FSMContext) -> None:
    await state.update_data(step_location=message.text.strip())
    await state.set_state(TravelCustDev.step_format)
    await message.answer(
        f"<b>Вопрос 2 из 7:</b>\n{QUESTIONS['step_format']}",
        parse_mode=ParseMode.HTML,
    )


@router.message(TravelCustDev.step_format, F.text)
async def process_format(message: Message, state: FSMContext) -> None:
    await state.update_data(step_format=message.text.strip())
    await state.set_state(TravelCustDev.step_stress)
    await message.answer(
        f"<b>Вопрос 3 из 7:</b>\n{QUESTIONS['step_stress']}",
        parse_mode=ParseMode.HTML,
    )


@router.message(TravelCustDev.step_stress, F.text)
async def process_stress(message: Message, state: FSMContext) -> None:
    await state.update_data(step_stress=message.text.strip())
    await state.set_state(TravelCustDev.step_infra)
    await message.answer(
        f"<b>Вопрос 4 из 7:</b>\n{QUESTIONS['step_infra']}",
        parse_mode=ParseMode.HTML,
    )


@router.message(TravelCustDev.step_infra, F.text)
async def process_infra(message: Message, state: FSMContext) -> None:
    await state.update_data(step_infra=message.text.strip())
    await state.set_state(TravelCustDev.step_overpay)
    await message.answer(
        f"<b>Вопрос 5 из 7:</b>\n{QUESTIONS['step_overpay']}",
        parse_mode=ParseMode.HTML,
    )


@router.message(TravelCustDev.step_overpay, F.text)
async def process_overpay(message: Message, state: FSMContext) -> None:
    await state.update_data(step_overpay=message.text.strip())
    await state.set_state(TravelCustDev.step_benchmark)
    await message.answer(
        f"<b>Вопрос 6 из 7:</b>\n{QUESTIONS['step_benchmark']}",
        parse_mode=ParseMode.HTML,
    )


@router.message(TravelCustDev.step_benchmark, F.text)
async def process_benchmark(message: Message, state: FSMContext) -> None:
    await state.update_data(step_benchmark=message.text.strip())
    await state.set_state(TravelCustDev.step_payment)
    await message.answer(
        f"<b>Вопрос 7 из 7:</b>\n{QUESTIONS['step_payment']}",
        parse_mode=ParseMode.HTML,
    )


@router.message(TravelCustDev.step_payment, F.text)
async def process_payment(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.update_data(step_payment=message.text.strip())
    data = await state.get_data()
    await state.clear()

    await message.answer(
        "Спасибо за ответы! Ваши инсайты помогут нам создать крутой продукт."
    )

    user = message.from_user
    user_id = user.id if user else 0
    username = f"@{user.username}" if user and user.username else "без username"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "username": user.username if user else None,
        "full_name": user.full_name if user else None,
        "answers": {
            "location": data.get("step_location", ""),
            "format": data.get("step_format", ""),
            "stress": data.get("step_stress", ""),
            "infra": data.get("step_infra", ""),
            "overpay": data.get("step_overpay", ""),
            "benchmark": data.get("step_benchmark", ""),
            "payment": data.get("step_payment", ""),
        },
    }

    try:
        await save_response_to_file(record)
    except Exception as exc:
        logging.error(f"Error saving response to JSON: {exc}")

    admin_text = (
        "🚀 <b>НОВЫЙ CUSTDEV-ОТВЕТ!</b>\n"
        f"👤 <b>Респондент:</b> {html.escape(username)} (ID: <code>{user_id}</code>)\n"
        f"📍 <b>1. Локация:</b> {html.escape(data.get('step_location', ''))}\n"
        f"👥 <b>2. Формат:</b> {html.escape(data.get('step_format', ''))}\n"
        f"⚠️ <b>3. Боль и стресс:</b> {html.escape(data.get('step_stress', ''))}\n"
        f"🛠 <b>4. Инфраструктура/Быт:</b> {html.escape(data.get('step_infra', ''))}\n"
        f"💸 <b>5. Переплаты:</b> {html.escape(data.get('step_overpay', ''))}\n"
        f"💡 <b>6. Бенчмарк/Идеи:</b> {html.escape(data.get('step_benchmark', ''))}\n"
        f"💰 <b>7. Готовность платить:</b> {html.escape(data.get('step_payment', ''))}"
    )

    try:
        await bot.send_message(
            chat_id=settings.admin_chat_id,
            text=admin_text,
            parse_mode=ParseMode.HTML,
        )
    except Exception as exc:
        logging.error(f"Error sending report to admin ({settings.admin_chat_id}): {exc}")
