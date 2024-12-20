
cmd-start =
   Спасибо, что решили воспользоваться <b>Panda Solve</b> 🐼

   <b>Бесплатно</b> ежедневно доступно <b>3</b> решения задач 🚀

   Теперь просто отправь <b>фотографию / скриншот</b> задания или напиши <b>текстом</b> ✍️

   В меню доступны следующие команды:

   • /donate: получить дополнительно еще одно решение от 🐼
   • /paysupport: помощь с донатом
   • /balance: текущий баланс

custom-donate-input-error = Пожалуйста, введите сумму в формате <code>/donate ЧИСЛО</code>, где ЧИСЛО от 1 до 2500 включительно.

invoice-title = Донат для 🐼

invoice-description-old =
    {$starsCount ->
        [one] {$starsCount} звезда
        [few] {$starsCount} звезды
       *[other] {$starsCount} звёзд
}

invoice-description = Получите еще одно решение от 🐼

pre-checkout-failed-reason = Нет больше места для денег 😭

cmd-paysupport =
    Здравствуйте! 🐼 Пожалуйста, если возникли проблемы с покупкой, напишите нам в поддержку @pandasolve_support

refund-successful =
    Возврат произведён успешно. Потраченные звёзды уже вернулись на ваш счёт в Telegram.

refund-no-code-provided =
    Пожалуйста, введите команду <code>/refund КОД</code>, где КОД – айди транзакции.
    Его можно увидеть после выполнения платежа, а также в разделе "Звёзды" в приложении Telegram.

refund-code-not-found =
    Такой код покупки не найден. Пожалуйста, проверьте вводимые данные и повторите ещё раз.

refund-already-refunded =
    За эту покупку уже ранее был произведён возврат средств.

refund-not-allowed = Возврат средств невозможен, используйте команду /paysupport для помощи.

payment-successful =
    <b>Огромное спасибо!</b>

    Вы получили <b>одну</b> дополнительную обработку изображения 🐼

    Ваш айди транзакции:
    <code>{$id}</code>

invoice-link-text =
    Воспользуйтесь <a href="{$link}">этой ссылкой</a> для доната в размере {$starsCount} звёзд.

loading-message =
Решаю задачу 🐼 Подождите ⏳

balance-info =
    🚀 <b>Ежедневный лимит:</b> {$daily_limit ->
        [one] {$daily_limit} ответ
        [few] {$daily_limit} ответа
       *[other] {$daily_limit} ответов
}
    ⭐️ <b>Донатный лимит:</b> {$donate_limit ->
        [one] {$donate_limit} ответ
        [few] {$donate_limit} ответа
       *[other] {$donate_limit} ответов
}

    Чтобы увеличить ⭐️ Донатный лимит ⭐ нажми /donate

notify-not-allowed = Извините, но вам не разрешена эта команда. Обратитесь к администратору.