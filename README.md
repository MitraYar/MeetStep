# MeetStep

MIDI-секвенсор для Windows, управляемый SMK 37 Pro и клавиатурой ПК.
Секвенсор задаёт MIDI Clock, DAW воспроизводит инструменты.

**[Полная спецификация →](SPECIFICATION.md)** · **[Текущий статус →](docs/PROJECT_STATUS.md)** · **[Карта контроллера →](docs/controller.md)**

Разработка сейчас ведётся в ветке [`build/smk-rgb-tester`](https://github.com/MitraYar/MeetStep/tree/build/smk-rgb-tester).
Название ветки историческое: актуальная работа — секвенсор. В `main` эти изменения пока не перенесены.

## Текущий прототип: 0.2.2

- 6 паттернов по 16 шагов, выход нот на MIDI-канале 1.
- Выбор ноты с клавиатуры SMK или мышью; пэды первой банки CH10 переключают шаги.
- Мышь: левая кнопка рисует, правая стирает, перетаскивание редактирует строку.
- Velocity от нажатия пэда сохраняется и воспроизводится; мышь создаёт шаг с velocity 100.
- Space и note 63 второй банки CH10/CH11 — Play/Pause. Start начинает заново.
- LED выбранной ноты: пустой шаг чёрный, velocity 127 синевато-белый, между ними градиент.
- Паттерны и BPM сохраняются при выходе; MIDI-устройства выбираются после каждого запуска.

Clear pattern / Clear all стирают данные сразу; Undo пока нет.
Это промежуточный прототип, а не полная реализация спецификации.

## Сборка и запуск

[GitHub Actions: Windows Standalone](https://github.com/MitraYar/MeetStep/actions/workflows/windows.yml)
собирает ZIP с EXE. Наличие исходников в ветке не означает, что конкретная сборка уже прошла.
[Установка и MIDI-маршрутизация](packaging/INSTALL-WINDOWS.txt).

Локально нужны Visual Studio 2022 с C++ и CMake; JUCE 8.0.6 закреплён в CMakeLists.txt:

```powershell
cmake -S . -B build -A x64 -DMEETSTEP_BUILD_STANDALONE=ON -DMEETSTEP_BUILD_PLUGIN=OFF -DBUILD_TESTING=OFF
cmake --build build --config Release --target MeetStepApp --parallel 2
```

## Границы работы

LED-утилиты функционируют и **заморожены**; VST3 также заморожен.
Подсветка интегрируется только в секвенсор. [Краткая справка по LED-протоколу](docs/protocol/LED.md)
содержит рабочий формат и ограничения. История экспериментов остаётся в Git.
