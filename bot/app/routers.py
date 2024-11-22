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

from tg_app import process_photo_message
from bot.constants import ADD_NEW_USER_ENDPOINT, PRICE_PER_IMAGE_IN_STARS, DONATE_ENDPOINT, NETWORK

router = Router()
logger = structlog.get_logger()


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
                f"http://{NETWORK}:8000{ADD_NEW_USER_ENDPOINT}",
                json=data
        ) as response:
            answer = await response.json()
            if response.status != 200:
                raise Exception(f"Failed to add new user. Status code: {response.status}")
        print(answer)
    await message.answer(l10n.format_value("cmd-start"))


@router.message(Command("donate"))
async def cmd_donate(
        message: Message,
        command: CommandObject,
        l10n: FluentLocalization,
):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=f"Оплатить {PRICE_PER_IMAGE_IN_STARS} XTR",
        pay=True
    )
    builder.button(
        text="Отменить покупку",
        callback_data="cancel"
    )
    builder.adjust(1)

    prices = [LabeledPrice(label="XTR", amount=PRICE_PER_IMAGE_IN_STARS)]
    await message.answer_invoice(
        title=l10n.format_value("invoice-title"),
        description=l10n.format_value(
            "invoice-description",
            {"starsCount": PRICE_PER_IMAGE_IN_STARS}
        ),
        prices=prices,
        provider_token="",
        payload=f"{PRICE_PER_IMAGE_IN_STARS}_stars",
        currency="XTR",
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == "cancel")
async def cancel_purchase(callback_query: CallbackQuery):
    # Delete the message containing the donation link
    await callback_query.message.delete()
    # Provide user feedback that the purchase was canceled
    await callback_query.answer("Покупка была отменена.")


@router.message(Command("paysupport"))
async def cmd_paysupport(
        message: Message,
        l10n: FluentLocalization
):
    await message.answer(l10n.format_value("cmd-paysupport"))


@router.message(Command("refund"))
async def cmd_refund(
        message: Message,
        bot: Bot,
        command: CommandObject,
        l10n: FluentLocalization,
):
    transaction_id = command.args
    if transaction_id is None:
        await message.answer(
            l10n.format_value("refund-no-code-provided")
        )
        return
    try:
        await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=transaction_id
        )
        await message.answer(
            l10n.format_value("refund-successful")
        )
    except TelegramBadRequest as error:
        if "CHARGE_NOT_FOUND" in error.message:
            text = l10n.format_value("refund-code-not-found")
        elif "CHARGE_ALREADY_REFUNDED" in error.message:
            text = l10n.format_value("refund-already-refunded")
        else:
            # При всех остальных ошибках – такой же текст,
            # как и в первом случае
            text = l10n.format_value("refund-code-not-found")
        await message.answer(text)
        return


@router.message(Command("donate_link"))
async def cmd_link(
        message: Message,
        bot: Bot,
        l10n: FluentLocalization,
):
    invoice_link = await bot.create_invoice_link(
        title=l10n.format_value("invoice-title"),
        description=l10n.format_value(
            "invoice-description",
            {"starsCount": PRICE_PER_IMAGE_IN_STARS}
        ),
        prices=[LabeledPrice(label="XTR", amount=PRICE_PER_IMAGE_IN_STARS)],
        provider_token="",
        payload="demo",
        currency="XTR"
    )
    await message.answer(
        l10n.format_value(
            "invoice-link-text",
            {"link": invoice_link, "starsCount": PRICE_PER_IMAGE_IN_STARS}
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
        user_username=message.from_user.username
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
                    }
            ) as response:
                answer = await response.json()
                if response.status != 200:
                    raise Exception(f"Failed to donate. Status code: {response.status}")
            print(answer)

        await message.answer(
            l10n.format_value(
                "payment-successful",
                {"id": message.successful_payment.telegram_payment_charge_id}
            ),
            # Fireworks!
            message_effect_id="5104841245755180586",
        )
    except Exception as e:
        await message.answer(
            l10n.format_value("payment-error")
        )
        await logger.aexception("Failed to process payment", exc_info=e)


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
            await message.answer(message.text)
    except Exception as e:
        print(f"Error: {e}")
        raise Exception(f"Error: {e}")
