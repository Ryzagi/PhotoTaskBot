import os

import structlog
from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import LabeledPrice, PreCheckoutQuery, CallbackQuery
from fluent.runtime import FluentLocalization
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import Bot, html
from aiogram.client.session import aiohttp
from aiogram.filters import CommandStart
from aiogram.types import Message

from tg_app import (
    process_photo_message,
    process_text_message,
    notify_all_users,
    notify_user,
    add_subscription_limits_for_all_users,
)
from bot.constants import (
    ADD_NEW_USER_ENDPOINT,
    PRICE_PER_IMAGE_IN_STARS,
    DONATE_ENDPOINT,
    NETWORK,
    GET_CURRENT_BALANCE_ENDPOINT,
    GET_ALL_USER_IDS,
)

router = Router()
logger = structlog.get_logger()

ADMIN_TG_ID = os.getenv("ADMIN_TG_ID")


@router.message(CommandStart())
async def command_start_handler(message: Message, l10n: FluentLocalization) -> None:
    """
    This handler receives messages with `/start` command
    """
    data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "language_code": message.from_user.language_code,
        "is_premium": message.from_user.is_premium,
        "is_bot": message.from_user.is_bot,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://{NETWORK}:8000{ADD_NEW_USER_ENDPOINT}", json=data
        ) as response:
            answer = await response.json()
            if response.status != 200:
                raise Exception(
                    f"Failed to add new user. Status code: {response.status}"
                )
        print(answer)
    await message.answer(l10n.format_value("cmd-start"))


@router.message(Command("donate"))
async def cmd_donate(
    message: Message,
    command: CommandObject,
    l10n: FluentLocalization,
):
    builder = InlineKeyboardBuilder()
    builder.button(text=f"Оплатить {PRICE_PER_IMAGE_IN_STARS} XTR", pay=True)
    builder.button(text="Отменить покупку", callback_data="cancel")
    builder.adjust(1)

    prices = [LabeledPrice(label="XTR", amount=PRICE_PER_IMAGE_IN_STARS)]
    await message.answer_invoice(
        title=l10n.format_value("invoice-title"),
        description=l10n.format_value("invoice-description", {"starsCount": PRICE_PER_IMAGE_IN_STARS}),
        prices=prices,
        provider_token="",
        payload=f"{PRICE_PER_IMAGE_IN_STARS}_stars",
        currency="XTR",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data == "cancel")
async def cancel_purchase(callback_query: CallbackQuery):
    # Delete the message containing the donation link
    await callback_query.message.delete()
    # Provide user feedback that the purchase was canceled
    await callback_query.answer("Покупка была отменена.")


@router.message(Command("paysupport"))
async def cmd_paysupport(message: Message, l10n: FluentLocalization):
    await message.answer(l10n.format_value("cmd-paysupport"))



USAGE_TEXT = "Usage:\n" + html.code("/refund CHARGE_ID USER_ID") + "\nOR\n" + html.code("/refund USER_ID:CHARGE_ID")

@router.message(Command("refund"))
async def cmd_refund(
    message: Message,
    bot: Bot,
    command: CommandObject,
    l10n: FluentLocalization,
):
    admin_id = str(message.from_user.id)
    if admin_id != ADMIN_TG_ID:
        await message.answer(l10n.format_value("refund-not-allowed"))
        return

    raw = (command.args or "").strip()
    if not raw:
        await message.answer(USAGE_TEXT)
        return

    payer_user_id = None
    charge_id = None

    if ":" in raw and " " not in raw:
        left, right = raw.split(":", 1)
        if left.isdigit():
            payer_user_id = int(left)
            charge_id = right.strip()
    else:
        parts = raw.split()
        if len(parts) == 2 and parts[1].isdigit():
            charge_id, payer_user_id = parts[0], int(parts[1])

    if charge_id:
        charge_id = charge_id.strip()
        if charge_id.startswith("{") and charge_id.endswith("}"):
            charge_id = charge_id[1:-1].strip()

    if not charge_id or not payer_user_id:
        await message.answer(USAGE_TEXT)
        return

    try:
        await bot.refund_star_payment(
            user_id=payer_user_id,
            telegram_payment_charge_id=charge_id,
        )
        await message.answer(
            l10n.format_value("refund-successful")
            + f" (user {payer_user_id}, charge {html.quote(charge_id)})"
        )
    except TelegramBadRequest as error:
        await logger.awarn(
            "Refund failed",
            charge_id=charge_id,
            payer_user_id=payer_user_id,
            tg_error=error.message,
        )
        if "CHARGE_NOT_FOUND" in error.message:
            text = l10n.format_value("refund-code-not-found")
        elif "CHARGE_ALREADY_REFUNDED" in error.message:
            text = l10n.format_value("refund-already-refunded")
        elif "CHARGE_ID_EMPTY" in error.message:
            text = l10n.format_value("refund-no-code-provided")
        else:
            text = l10n.format_value("refund-code-not-found")
        await message.answer(text)


@router.message(Command("donate_link"))
async def cmd_link(
    message: Message,
    bot: Bot,
    l10n: FluentLocalization,
):
    invoice_link = await bot.create_invoice_link(
        title=l10n.format_value("invoice-title"),
        description=l10n.format_value(
            "invoice-description", {"starsCount": PRICE_PER_IMAGE_IN_STARS}
        ),
        prices=[LabeledPrice(label="XTR", amount=PRICE_PER_IMAGE_IN_STARS)],
        provider_token="",
        payload="demo",
        currency="XTR",
    )
    await message.answer(
        l10n.format_value(
            "invoice-link-text",
            {"link": invoice_link, "starsCount": PRICE_PER_IMAGE_IN_STARS},
        )
    )


@router.pre_checkout_query()
async def on_pre_checkout_query(
    pre_checkout_query: PreCheckoutQuery,
    l10n: FluentLocalization,
):
    await pre_checkout_query.answer(ok=True)

    # If you want to reject the payment, you can do it like this:
    # await pre_checkout_query.answer(
    #     ok=False,
    #     error_message=l10n.format_value("pre-checkout-failed-reason")
    # )


@router.message(F.successful_payment)
async def on_successful_payment(
    message: Message,
    l10n: FluentLocalization,
):
    await logger.ainfo(
        "Получен новый донат!",
        amount=message.successful_payment.total_amount,
        from_user_id=message.from_user.id,
        user_username=message.from_user.username,
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"http://{NETWORK}:8000{DONATE_ENDPOINT}",
                json={
                    "user_id": message.from_user.id,
                    "username": message.from_user.username,
                    "first_name": message.from_user.first_name,
                    "last_name": message.from_user.last_name,
                    "language_code": message.from_user.language_code,
                    "is_premium": message.from_user.is_premium,
                    "is_bot": message.from_user.is_bot,
                },
            ) as response:
                answer = await response.json()
                if response.status != 200:
                    raise Exception(f"Failed to donate. Status code: {response.status}")
            print(answer)

        await message.answer(
            l10n.format_value(
                "payment-successful",
                {"id": message.successful_payment.telegram_payment_charge_id},
            ),
            # Fireworks!
            message_effect_id="5104841245755180586",
        )
    except Exception as e:
        await message.answer(l10n.format_value("payment-error"))
        await logger.aexception("Failed to process payment", exc_info=e)


@router.message(Command("balance"))
async def cmd_balance(message: Message, l10n: FluentLocalization):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"http://{NETWORK}:8000{GET_CURRENT_BALANCE_ENDPOINT}",
            json={"user_id": str(message.from_user.id)},
        ) as response:
            answer = await response.json()
            print("ANSWER", answer)
            if response.status != 200:
                raise Exception(
                    f"Failed to get balance. Status code: {response.status}"
                )
    limits = answer["message"]
    daily_limit = limits[0]["daily_limit"]
    subscription_limit = limits[0]["subscription_limit"]
    print(daily_limit, subscription_limit)
    print(
        l10n.format_value(
            "balance-info",
            {"daily_limit": int(daily_limit), "donate_limit": int(subscription_limit)},
        )
    )
    await message.answer(
        l10n.format_value(
            "balance-info",
            {"daily_limit": int(daily_limit), "donate_limit": int(subscription_limit)},
        )
    )


@router.message(Command("notify_all"))
async def cmd_notify_all(message: Message, l10n: FluentLocalization):
    user_id = str(message.from_user.id)
    if user_id != ADMIN_TG_ID:
        await message.answer(l10n.format_value("notify-not-allowed"))
        return
    await notify_all_users(message)


@router.message(Command("notify_user"))
async def cmd_notify_user(message: Message, l10n: FluentLocalization):
    user_id = str(message.from_user.id)
    if user_id != ADMIN_TG_ID:
        await message.answer(l10n.format_value("notify-not-allowed"))
        return
    await notify_user(message)


@router.message(Command("add_subscription_limits_for_all_users"))
async def cmd_add_subscription_limits_for_all_users(
    message: Message, l10n: FluentLocalization
):
    user_id = str(message.from_user.id)
    if user_id != ADMIN_TG_ID:
        await message.answer(l10n.format_value("notify-not-allowed"))
        return
    limit = message.text.split(" ")[1]
    await add_subscription_limits_for_all_users(limit)


@router.message()
async def message_handler(message: Message) -> None:
    """
    Handler will forward receive a message back to the sender
    Args:
        message: Message: Received message object
    Return None
    """
    try:
        if message.photo:
            await process_photo_message(message)
        elif message.text:
            await process_text_message(message)
    except Exception as e:
        print(f"Error: {e}")
        raise Exception(f"Error: {e}")
