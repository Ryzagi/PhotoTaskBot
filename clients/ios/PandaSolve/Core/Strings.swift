import SwiftUI
import Observation

// In-app localization, ported from Android i18n/Localization.kt — the language
// toggle flips the whole tree live via the environment (RU default source).
struct Strings {
    var navHome = "главная", navProfile = "профиль"
    var welcomeBack = "с возвращением,", bambooToday = "БАМБУК НА СЕГОДНЯ"
    var dailyFreeHint = "🎋 3 решения бесплатно каждый день"
    var daysShort = "дн.", searchHint = "поиск по решениям…"
    var noTasks = "Пока нет решений — реши первую задачу 🐼"
    var searchEmpty = "Ничего не нашлось — попробуй иначе 🐼"
    var dayToday = "сегодня", dayYesterday = "вчера"
    var all = "все →", filterAll = "все", untitled = "Без названия"
    var statusSolved = "решено", statusTalking = "беседа"
    // profile
    var profileTitle = "Профиль", statStreak = "дней стрик", statSolved = "решено", statAlbums = "папок"
    var achievements = "Достижения 🏆"
    var rowTopUp = "Пополнить бамбук", rowTopUpHint = "пакеты 20 · 50 · 100"
    var rowLanguage = "Язык", rowTheme = "Тема"
    var themeSystem = "Как в системе", themeLight = "Светлая", themeDark = "Тёмная"
    var rowSolveMode = "Режим", solveModeSolve = "Решение", solveModeExplain = "Объяснение"
    var rowNotifications = "Уведомления", notificationsHint = "решения и ответы"
    var rowSignOut = "Выйти"
    // albums
    var albumNewTitle = "Новая папка ✨", albumEditTitle = "Папка ✏️"
    var albumNameLabel = "НАЗВАНИЕ", albumNameHint = "например, Химия"
    var albumIconLabel = "ЗНАЧОК", albumColorLabel = "ЦВЕТ"
    var albumCreate = "Создать", albumSave = "Сохранить", albumDelete = "Удалить", cancel = "Отмена"
    var albumPickerTitle = "В какую папку? 🗂️", albumNone = "Без папки"
    var albumPickerEmpty = "Пока нет папок — создай их на главном экране (＋)."
    // task actions
    var taskRename = "✏️ Переименовать", renameHint = "Название задачи", save = "Сохранить"
    var taskAssignAlbum = "📁 В папку", taskActionsTitle = "Что сделать?"
    // chat
    var chatRemainingFmt = "осталось %d"
    var chatLimitReached = "Бесплатные вопросы закончились — пополни бамбук 🎋"
    var chatTopUp = "Пополнить", chatPaidHint = "дальше: 1 вопрос = 1 🎋"
    // sign-in
    var signinGreeting = "Приве-е-ет! ✿", signinTitle = "Давай решать\nвместе"
    var signinSubtitle = "Сфоткай задачу — я объясню по шагам."
    var fieldEmail = "почта", fieldPassword = "пароль"
    var signinButton = "Войти 🚀", orDivider = "ИЛИ"
    var signinTerms = "Войдя, ты соглашаешься с правилами и конфиденциальностью."
    var privacyPolicy = "Политика конфиденциальности"
    var tabSignIn = "Вход", tabSignUp = "Регистрация", signupButton = "Создать аккаунт 🐼"
    var checkInbox = "Мы отправили ссылку для подтверждения на твою почту. Подтверди её и войди 🐼"
    var soon = "скоро"
    // auth errors
    var errEmptyFields = "Заполни почту и пароль", errInvalidCredentials = "Неверная почта или пароль"
    var errUserExists = "Аккаунт с такой почтой уже есть — войди"
    var errWeakPassword = "Пароль слишком короткий — минимум 6 символов"
    var errInvalidEmail = "Проверь формат почты", errEmailNotConfirmed = "Почта не подтверждена — проверь письмо"
    var errRateLimited = "Слишком много попыток — попробуй чуть позже"
    var errNetwork = "Нет связи — проверь интернет", errUnknown = "Что-то пошло не так — попробуй ещё раз"
    // camera / solve
    var solveProblemLabel = "УСЛОВИЕ"
    var solveTextPlaceholder = "Напиши условие задачи…\nнапример: реши x² − 5x + 6 = 0"
    var cameraPermTitle = "Дай доступ к камере 🐼", cameraPermSubtitle = "чтобы сфотографировать задачу"
    var cameraPermAllow = "Разрешить", cameraOrType = "или напиши текстом →"
    var cameraAim = "наведи на задачу ✏️", cameraReady = "панда готова"
    var modeText = "ТЕКСТ", modePhoto = "ФОТО"
    var solvingPanda = "Панда решает… 🐼", captionPlaceholder = "Добавь подпись… (необязательно)"
    // task detail
    var answerLabel = "✓ ОТВЕТ", revealAnswer = "👀 Нажми, чтобы открыть ответ"
    var taskTitleFallback = "Задача", secondsShort = "сек"
    var chooseFolder = "выбрать папку", solvingLabel = "🐼 решаю…"
    var solvingStep = "Панда читает условие и думает над решением…"
    var solutionLabel = "📝 решение", askPandaLabel = "💬 спроси панду"
    var chatEmptyHint = "Задай уточняющий вопрос по решению выше 🐼"
    var pandaTyping = "панда печатает…", askMore = "спросить ещё…"
    var taskLoadFailed = "Не удалось загрузить задачу"
    var topUpUnavailable = "Пакеты пока доступны в Android-версии — скоро и здесь 🐼"

    static let ru = Strings()
    static let en: Strings = {
        var s = Strings()
        s.navHome = "home"; s.navProfile = "profile"
        s.welcomeBack = "welcome back,"; s.bambooToday = "BAMBOO FOR TODAY"
        s.dailyFreeHint = "🎋 3 free solutions every day"
        s.daysShort = "d."; s.searchHint = "search solutions…"
        s.noTasks = "No solutions yet — solve your first one 🐼"
        s.searchEmpty = "Nothing here — try another search 🐼"
        s.dayToday = "today"; s.dayYesterday = "yesterday"
        s.all = "all →"; s.filterAll = "all"; s.untitled = "Untitled"
        s.statusSolved = "solved"; s.statusTalking = "chat"
        s.profileTitle = "Profile"; s.statStreak = "day streak"; s.statSolved = "solved"; s.statAlbums = "folders"
        s.achievements = "Achievements 🏆"
        s.rowTopUp = "Top up bamboo"; s.rowTopUpHint = "packs 20 · 50 · 100"
        s.rowLanguage = "Language"; s.rowTheme = "Theme"
        s.themeSystem = "System"; s.themeLight = "Light"; s.themeDark = "Dark"
        s.rowSolveMode = "Mode"; s.solveModeSolve = "Solve"; s.solveModeExplain = "Explain"
        s.rowNotifications = "Notifications"; s.notificationsHint = "solutions and replies"
        s.rowSignOut = "Sign out"
        s.albumNewTitle = "New folder ✨"; s.albumEditTitle = "Folder ✏️"
        s.albumNameLabel = "NAME"; s.albumNameHint = "e.g., Chemistry"
        s.albumIconLabel = "ICON"; s.albumColorLabel = "COLOR"
        s.albumCreate = "Create"; s.albumSave = "Save"; s.albumDelete = "Delete"; s.cancel = "Cancel"
        s.albumPickerTitle = "Which folder? 🗂️"; s.albumNone = "No folder"
        s.albumPickerEmpty = "No folders yet — create one on Home (＋)."
        s.taskRename = "✏️ Rename"; s.renameHint = "Task title"; s.save = "Save"
        s.taskAssignAlbum = "📁 To folder"; s.taskActionsTitle = "What to do?"
        s.chatRemainingFmt = "%d left"
        s.chatLimitReached = "Free questions used up — top up bamboo 🎋"
        s.chatTopUp = "Top up"; s.chatPaidHint = "next: 1 question = 1 🎋"
        s.signinGreeting = "Hi there! ✿"; s.signinTitle = "Let's solve\ntogether"
        s.signinSubtitle = "Snap a problem — I'll explain step by step."
        s.fieldEmail = "email"; s.fieldPassword = "password"
        s.signinButton = "Sign in 🚀"; s.orDivider = "OR"
        s.signinTerms = "By signing in you agree to the terms and privacy policy."
        s.privacyPolicy = "Privacy Policy"
        s.tabSignIn = "Sign in"; s.tabSignUp = "Sign up"; s.signupButton = "Create account 🐼"
        s.checkInbox = "We've sent a confirmation link to your email. Confirm it, then sign in 🐼"
        s.soon = "soon"
        s.errEmptyFields = "Enter your email and password"; s.errInvalidCredentials = "Wrong email or password"
        s.errUserExists = "An account with this email already exists — sign in"
        s.errWeakPassword = "Password is too short — at least 6 characters"
        s.errInvalidEmail = "Check the email format"; s.errEmailNotConfirmed = "Email not confirmed — check your inbox"
        s.errRateLimited = "Too many attempts — try again a bit later"
        s.errNetwork = "No connection — check your internet"; s.errUnknown = "Something went wrong — try again"
        s.solveProblemLabel = "PROBLEM"
        s.solveTextPlaceholder = "Type the problem…\ne.g. solve x² − 5x + 6 = 0"
        s.cameraPermTitle = "Allow camera access 🐼"; s.cameraPermSubtitle = "to photograph the problem"
        s.cameraPermAllow = "Allow"; s.cameraOrType = "or type it instead →"
        s.cameraAim = "aim at the problem ✏️"; s.cameraReady = "panda ready"
        s.modeText = "TEXT"; s.modePhoto = "PHOTO"
        s.solvingPanda = "Panda is solving… 🐼"; s.captionPlaceholder = "Add a caption… (optional)"
        s.answerLabel = "✓ ANSWER"; s.revealAnswer = "👀 Tap to reveal the answer"
        s.taskTitleFallback = "Task"; s.secondsShort = "s"
        s.chooseFolder = "choose folder"; s.solvingLabel = "🐼 solving…"
        s.solvingStep = "The panda is reading the problem and working it out…"
        s.solutionLabel = "📝 solution"; s.askPandaLabel = "💬 ask the panda"
        s.chatEmptyHint = "Ask a follow-up about the solution above 🐼"
        s.pandaTyping = "the panda is typing…"; s.askMore = "ask something…"
        s.taskLoadFailed = "Couldn't load the task"
        s.topUpUnavailable = "Packs are on Android for now — coming here soon 🐼"
        return s
    }()

    static func forCode(_ code: String) -> Strings { code.lowercased().hasPrefix("en") ? .en : .ru }
}

private struct StringsKey: EnvironmentKey { static let defaultValue = Strings.ru }
extension EnvironmentValues { var strings: Strings { get { self[StringsKey.self] } set { self[StringsKey.self] = newValue } } }

// MARK: - Persisted preferences (UserDefaults; flips the tree live)

@Observable final class AppPrefs {
    static let shared = AppPrefs()
    var language: String { didSet { UserDefaults.standard.set(language, forKey: "ui_language") } }
    var theme: String { didSet { UserDefaults.standard.set(theme, forKey: "ui_theme") } }         // system|light|dark
    var solveMode: String { didSet { UserDefaults.standard.set(solveMode, forKey: "solve_mode") } } // solve|explain
    var notifEnabled: Bool { didSet { UserDefaults.standard.set(notifEnabled, forKey: "notif_enabled") } }

    private init() {
        language = UserDefaults.standard.string(forKey: "ui_language")
            ?? (Locale.preferredLanguages.first?.hasPrefix("ru") == true ? "ru" : "en")
        theme = UserDefaults.standard.string(forKey: "ui_theme") ?? "system"
        solveMode = UserDefaults.standard.string(forKey: "solve_mode") ?? "solve"
        notifEnabled = UserDefaults.standard.object(forKey: "notif_enabled") as? Bool ?? true
    }
}

// MARK: - Friendly auth errors (ported from Android auth/AuthError.kt)

enum AuthUIError { case emptyFields, invalidCredentials, userExists, weakPassword, invalidEmail, emailNotConfirmed, rateLimited, network, cancelled, unknown

    static func from(_ error: Error) -> AuthUIError {
        let msg = String(describing: error).lowercased()
        if error is URLError || msg.contains("network") || msg.contains("timed out") || msg.contains("connect") { return .network }
        if msg.contains("cancel") { return .cancelled }
        if msg.contains("already registered") || msg.contains("already exists") || msg.contains("user_already_exists") { return .userExists }
        if msg.contains("not confirmed") || msg.contains("email_not_confirmed") { return .emailNotConfirmed }
        if msg.contains("weak_password") || (msg.contains("password") && (msg.contains("least") || msg.contains("short"))) { return .weakPassword }
        if msg.contains("invalid login credentials") || msg.contains("invalid_credentials") { return .invalidCredentials }
        if msg.contains("invalid email") || msg.contains("invalid format") || msg.contains("validate email") { return .invalidEmail }
        if msg.contains("rate limit") || msg.contains("too many") || msg.contains("over_email_send_rate_limit") { return .rateLimited }
        return .unknown
    }

    func text(_ t: Strings) -> String? {
        switch self {
        case .emptyFields: return t.errEmptyFields
        case .invalidCredentials: return t.errInvalidCredentials
        case .userExists: return t.errUserExists
        case .weakPassword: return t.errWeakPassword
        case .invalidEmail: return t.errInvalidEmail
        case .emailNotConfirmed: return t.errEmailNotConfirmed
        case .rateLimited: return t.errRateLimited
        case .network: return t.errNetwork
        case .cancelled: return nil
        case .unknown: return t.errUnknown
        }
    }
}

// MARK: - Local-date helpers (ported from Android util/Dates.kt)

enum Dates {
    private static let iso: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter(); f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]; return f
    }()
    private static let isoPlain: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter(); f.formatOptions = [.withInternetDateTime]; return f
    }()

    static func parse(_ s: String) -> Date? { iso.date(from: s) ?? isoPlain.date(from: s) }

    /// Device-local "yyyy-MM-dd" for grouping/labelling.
    static func localDay(_ isoString: String) -> String {
        guard let d = parse(isoString) else { return String(isoString.prefix(10)) }
        let c = Calendar.current.dateComponents([.year, .month, .day], from: d)
        return String(format: "%04d-%02d-%02d", c.year!, c.month!, c.day!)
    }

    static func localTime(_ isoString: String) -> String {
        guard let d = parse(isoString) else { return "" }
        let c = Calendar.current.dateComponents([.hour, .minute], from: d)
        return String(format: "%02d:%02d", c.hour!, c.minute!)
    }

    static func solveSeconds(_ start: String, _ end: String) -> Int? {
        guard let a = parse(start), let b = parse(end) else { return nil }
        let s = Int(b.timeIntervalSince(a))
        return (0...86_400).contains(s) ? s : nil
    }

    static func todayYesterday() -> (String, String) {
        let now = Date()
        let f = { (d: Date) -> String in
            let c = Calendar.current.dateComponents([.year, .month, .day], from: d)
            return String(format: "%04d-%02d-%02d", c.year!, c.month!, c.day!)
        }
        return (f(now), f(Calendar.current.date(byAdding: .day, value: -1, to: now)!))
    }

    private static let ruMonths = ["января", "февраля", "марта", "апреля", "мая", "июня",
                                   "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    private static let enMonths = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    /// "2026-05-30" → "30 мая" / "May 30".
    static func pretty(_ day: String, en: Bool) -> String {
        let p = day.split(separator: "-")
        guard p.count == 3, let m = Int(p[1]), let d = Int(p[2]), (1...12).contains(m) else { return day }
        return en ? "\(enMonths[m - 1]) \(d)" : "\(d) \(ruMonths[m - 1])"
    }
}
