import AppKit

let outPath = "report_assets/таблица_5_1_1_сопоставление_целей_finpulse_full.png"
let width = 2400
let height = 1500

func color(_ hex: UInt32) -> NSColor {
    let r = CGFloat((hex >> 16) & 0xff) / 255.0
    let g = CGFloat((hex >> 8) & 0xff) / 255.0
    let b = CGFloat(hex & 0xff) / 255.0
    return NSColor(calibratedRed: r, green: g, blue: b, alpha: 1)
}

func rect(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat, _ fill: NSColor, _ stroke: NSColor? = nil, radius: CGFloat = 0, lineWidth: CGFloat = 2) {
    let path = NSBezierPath(roundedRect: NSRect(x: x, y: y, width: w, height: h), xRadius: radius, yRadius: radius)
    fill.setFill()
    path.fill()
    if let stroke {
        stroke.setStroke()
        path.lineWidth = lineWidth
        path.stroke()
    }
}

func text(_ value: String, _ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat, size: CGFloat, weight: NSFont.Weight = .regular, fill: NSColor = color(0x111827), align: NSTextAlignment = .left) {
    let paragraph = NSMutableParagraphStyle()
    paragraph.lineBreakMode = .byWordWrapping
    paragraph.alignment = align
    paragraph.lineSpacing = 4
    let font = NSFont.systemFont(ofSize: size, weight: weight)
    let attrs: [NSAttributedString.Key: Any] = [
        .font: font,
        .foregroundColor: fill,
        .paragraphStyle: paragraph
    ]
    NSString(string: value).draw(in: NSRect(x: x, y: y, width: w, height: h), withAttributes: attrs)
}

func line(_ x1: CGFloat, _ y1: CGFloat, _ x2: CGFloat, _ y2: CGFloat, _ stroke: NSColor = color(0xe2e8f0), _ lineWidth: CGFloat = 2) {
    let p = NSBezierPath()
    p.move(to: NSPoint(x: x1, y: y1))
    p.line(to: NSPoint(x: x2, y: y2))
    stroke.setStroke()
    p.lineWidth = lineWidth
    p.stroke()
}

let image = NSImage(size: NSSize(width: width, height: height))
image.lockFocusFlipped(true)

color(0xf6f8fb).setFill()
NSRect(x: 0, y: 0, width: width, height: height).fill()

rect(64, 54, 2272, 1392, color(0xffffff), color(0xd8e0ea), radius: 24, lineWidth: 3)

text("Таблица 5.1.1 - Сопоставление целей проекта с реализованным функционалом FinPulse", 110, 112, 2180, 58, size: 44, weight: .bold)
text("Итоговая проверка показывает, какие требования MVP закрыты в реализованной системе", 110, 176, 2180, 34, size: 28, fill: color(0x526174))

let x0: CGFloat = 110
let tableW: CGFloat = 2180
let top: CGFloat = 260
let headerH: CGFloat = 78
let rowH: CGFloat = 126
let lastRowH: CGFloat = 154
let c1: CGFloat = 520
let c2: CGFloat = 860
let c3: CGFloat = 520
let c4: CGFloat = 280
let x1 = x0 + c1
let x2 = x1 + c2
let x3 = x2 + c3

rect(x0, top, tableW, headerH, color(0x07111f), nil, radius: 14)
text("Цель / требование", x0 + 28, top + 22, c1 - 56, 38, size: 29, weight: .bold, fill: .white)
text("Реализация в FinPulse", x1 + 28, top + 22, c2 - 56, 38, size: 29, weight: .bold, fill: .white)
text("Подтверждение", x2 + 28, top + 22, c3 - 56, 38, size: 29, weight: .bold, fill: .white)
text("Статус", x3 + 28, top + 22, c4 - 56, 38, size: 29, weight: .bold, fill: .white)

line(x1, top, x1, top + headerH + rowH * 6 + lastRowH, color(0xcbd5e1), 3)
line(x2, top, x2, top + headerH + rowH * 6 + lastRowH, color(0xcbd5e1), 3)
line(x3, top, x3, top + headerH + rowH * 6 + lastRowH, color(0xcbd5e1), 3)

let rows: [(String, String, String, NSColor, CGFloat)] = [
    ("Получение новостей рынка РФ", "Публичная RSS-лента новостей с сохранением обработанных материалов", "Разделы 3.2, 4.1; публичная лента новостей", color(0xeff6ff), rowH),
    ("Структурированная карточка", "Карточка содержит summary, facts, market meaning, risks и indicator", "Скрины карточек; разделы 2.2, 3.2", color(0xf8fafc), rowH),
    ("AI-анализ и резервный режим", "GigaChat формирует JSON-карточку, rules-анализ используется как fallback", "Листинги 2.2.1, 2.2.3; раздел 4.3", color(0xecfdf5), rowH),
    ("Диалоговый ассистент", "Чат на Ollama, история сообщений, проверка и восстановление ответа", "Раздел 3.3; скрины чата", color(0xf8fafc), rowH),
    ("Пользовательский контекст", "Профиль хранит горизонт, опыт, риск, тикеры и сектора для контекста чата", "Разделы 3.3, 3.4; скрины профиля", color(0xf5f3ff), rowH),
    ("Рыночные данные MOEX", "Котировки IMOEX, динамика бумаг, лидер роста и лидер снижения", "Раздел 3.4.6; скрины MOEX", color(0xf8fafc), rowH),
    ("Доступность и безопасность", "JWT-авторизация, роли и permissions, desktop-сборка Tauri и мобильное представление на телефоне", "Разделы 3.1.4, 4.1, 4.2; свойства FinPulse.app, скрины телефона", color(0xfffbeb), lastRowH)
]

var y = top + headerH
for row in rows {
    rect(x0, y, tableW, row.4, row.3)
    line(x0, y, x0 + tableW, y, color(0xe2e8f0), 2)
    text(row.0, x0 + 28, y + 34, c1 - 56, row.4 - 40, size: 28, weight: .bold)
    text(row.1, x1 + 28, y + 28, c2 - 56, row.4 - 32, size: 25, fill: color(0x334155))
    text(row.2, x2 + 28, y + 28, c3 - 56, row.4 - 32, size: 25, fill: color(0x334155))
    rect(x3 + 42, y + (row.4 - 48) / 2, 178, 48, color(0xdcfce7), color(0x86efac), radius: 24, lineWidth: 2)
    text("Выполнено", x3 + 60, y + (row.4 - 30) / 2, 142, 32, size: 22, weight: .bold, fill: color(0x047857), align: .center)
    y += row.4
}

rect(x0, y + 48, tableW, 70, color(0xeef2ff), color(0xc7d2fe), radius: 16, lineWidth: 2)
text("Итог:", x0 + 28, y + 68, 90, 34, size: 27, weight: .bold)
text("ключевые цели MVP достигнуты; система реализует полный цикл от получения новости до аналитической интерпретации и диалогового уточнения.", x0 + 120, y + 68, tableW - 160, 34, size: 25, fill: color(0x334155))

image.unlockFocus()

guard let tiff = image.tiffRepresentation,
      let rep = NSBitmapImageRep(data: tiff),
      let data = rep.representation(using: .png, properties: [:]) else {
    fatalError("Cannot create PNG")
}

try data.write(to: URL(fileURLWithPath: outPath))
print(outPath)
