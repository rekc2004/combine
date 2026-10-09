# Профили моделей: откуда они взяты

Данные собраны 2026-10-09 по страницам Anthropic и независимым измерениям. **Это снимок, а не истина:** цифры вендора и независимые расходятся, а сами модели меняются. Профили в `core/models.json` это выжимка отсюда. Правьте их по собственному опыту.

Общее у всех четырёх моделей: контекст 1M токенов, вывод до 128K, effort поддерживают все ([Models overview](https://platform.claude.com/docs/en/models/overview)).

## Цены и характеристики
| Модель | Цена за 1M токенов (вход / выход) | Скорость | Слабые места по официальным источникам |
|---|---|---|---|
| Fable 5.1 | 10 / 50 | самая медленная | Самая дорогая; независимый индекс Artificial Analysis ниже, чем у Opus и Sonnet; запросы на пентест/эксплойты маршрутизируются на Opus |
| Opus 5.5 | 4 / 20 | средняя | Thinking нельзя отключить; иногда подозревает, что его тестируют |
| Sonnet 5.5 | 2 / 10 | быстрая | На max effort расходует очень много токенов и местами хуже, чем на xhigh |
| Haiku 5.5 | 0,10 / 0,50 (до 100K токенов в промпте; выше 0,50 / 2,50) | самая быстрая | На low effort с длинным системным промптом может остановиться раньше времени; может отчитаться об изменении без проверки; может пропустить нужный поиск ([prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-haiku-5-5)) |

Источники: страницы моделей [Fable 5.1](https://platform.claude.com/docs/en/models/fable-5-1/overview), [Opus 5.5](https://platform.claude.com/docs/en/models/opus-5-5/overview), [Sonnet 5.5](https://platform.claude.com/docs/en/models/sonnet-5-5/overview), [Haiku 5.5](https://platform.claude.com/docs/en/models/haiku-5-5/overview) и анонсы [Opus](https://www.anthropic.com/claude-opus-5-5), [Sonnet](https://www.anthropic.com/claude-sonnet-5-5), [Haiku](https://www.anthropic.com/claude-haiku-5-5), [Fable](https://www.anthropic.com/claude-fable-and-mythos-5-1). Цена кэш-чтения Sonnet в разных источниках расходится (0,10 или 0,20); для маршрутизации не критично.

## Бенчмарки: вендор против независимых
**Заявлено Anthropic** (сравнивать можно только внутри одного анонса, условия запусков различаются): Terminal-Bench 4.0 — Sonnet 5.5 70,6%, Opus 5.5 66,4%, Fable 5.1 55,8%, Haiku 5.5 39,2%. FrontierCode: Opus 54,4%, Sonnet 52,1% (на xhigh; на max 46,2%), Haiku 46,4%, Fable 50,3%. Источник: анонсы выше. SWE-bench на страницах Anthropic по этим моделям найти не удалось.

**Независимо** ([Artificial Analysis](https://artificialanalysis.ai/providers/anthropic), общий индекс при max effort): Opus 58, Sonnet 56, Fable 53, Haiku 43. [AA о Haiku 5.5](https://artificialanalysis.ai/articles/claude-haiku-5-5): Terminal-Bench 33% (вендор заявил 39,2%), доля выдуманных ответов в тесте AA-Omniscience 40%.

Что из этого следует и чего не следует: Fable не «лучше всех» на общем индексе, её сила в очень длинных агентных сессиях (вендор). Вывод «Sonnet лучше Opus в терминале» делать нельзя: у цифр разные условия и погрешность.

## Что рекомендует Anthropic про распределение задач
Источники: [Choosing a model](https://platform.claude.com/docs/en/about-claude/models/choosing-a-model), [Optimizing for cost and intelligence](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence), [Effort](https://platform.claude.com/docs/en/build-with-claude/effort).
- Для большинства сложных задач начинать с Opus 5.5, на Fable переходить, если Opus на xhigh/max не хватает.
- Настройка effort часто важнее смены модели. Субагентам типично low.
- Координатор Fable 5.1 над рабочими Sonnet 5 в их измерениях дешевле одиночной Fable на 47–55%, но на 10–12 пунктов точнее ниже. Для одной цепочки зависимых шагов лучше одна модель на низком effort.
- Исполнитель-Haiku/Sonnet с советником без явной инструкции советника не вызывал ни разу из 198 вопросов. Вывод для нас: **дешёвым агентам нужны явные инструкции, когда и что проверять**, на авось они не обратятся за помощью.
- Прямой рекомендации «сильная планирует, Haiku исполняет» в официальных источниках не найдено. Наша схема «скелет Haiku, проверка, потом сильные» это наша гипотеза: проверяйте её на своих задачах.

## Не удалось проверить
Системные карты (PDF больше 10 МБ) не открылись. Данные о доступности Fable (ограничения по экспорту) только из вторичного источника. Страницы лидербордов Arena читались через пересказы.
