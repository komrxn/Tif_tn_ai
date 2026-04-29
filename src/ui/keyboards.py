from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from src.ui.i18n import Lang, t


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
            ]
        ]
    )


def main_keyboard(lang: Lang) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=t(lang, "btn_search")),
                KeyboardButton(text=t(lang, "btn_history")),
            ],
            [
                KeyboardButton(text=t(lang, "btn_language")),
                KeyboardButton(text=t(lang, "btn_help")),
            ],
        ],
        resize_keyboard=True,
    )


def result_keyboard(lang: Lang, code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=t(lang, "btn_duties"), callback_data=f"duties:{code}"),
                InlineKeyboardButton(text=t(lang, "btn_tree"), callback_data=f"tree:{code}"),
            ],
            [
                InlineKeyboardButton(text=t(lang, "btn_explanation"), callback_data=f"expl:{code}"),
                InlineKeyboardButton(
                    text=t(lang, "btn_examples"), callback_data=f"examples:{code}"
                ),
            ],
        ]
    )


def back_keyboard(lang: Lang, code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data=f"back:{code}")]
        ]
    )


def skip_keyboard(lang: Lang) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "btn_skip"), callback_data="skip_clarify")]
        ]
    )
