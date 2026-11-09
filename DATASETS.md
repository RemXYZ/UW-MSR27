# Zbiory do wykrywania szkodliwych skilli i specyfikacji agentowych

| Zbiór | Dane i etykiety |
|---|---|
| [MaliciousSkillBench](https://huggingface.co/datasets/ProtectSkills/MaliciousSkillBench) | 7 505 skilli złośliwych i 2 235 bezpiecznych według etykiet autorów. Teksty i gotowy podział `Source-Disjoint` do testowania na nowych źródłach. |
| [SkillTrustBench](https://huggingface.co/datasets/cuhk-zhuque/SkillTrustBench) | 5 520 pakietów ze skryptami. Wersja 1.0 wyróżnia 2 863 złośliwe, 1 014 ryzykownych bez wyraźnej intencji ataku i 1 643 neutralne. Wiele przykładów jest syntetycznych. |
| [ClawHub Security Signals](https://huggingface.co/datasets/OpenClaw/clawhub-security-signals) | 67 453 wersje skilli z publicznego rejestru. Werdykty skanerów nadają się do uczenia ze słabymi etykietami. |
| [MaliciousAgentSkillsBench](https://huggingface.co/datasets/ProtectSkills/MaliciousAgentSkillsBench) | 157 rzeczywistych skilli o złośliwości potwierdzonej behawioralnie. Publiczne CSV zawierają metadane i typy zagrożeń, bez treści tych skilli. |
| [GitSkills](https://huggingface.co/datasets/mvaccargiu/gitskills) **(MSR 2027 Mining Challenge)** | 3 797 117 wystąpień plików skilli w 282 200 repozytoriach, w tym 1 877 981 unikatowych treści. Brak etykiet szkodliwości. |
| [SpecMine](https://doi.org/10.5281/zenodo.22102779) **(MSR 2027 Mining Challenge)** | 470 795 plików `spec.md` lub `specs.md` z 73 030 repozytoriów, bez etykiet szkodliwości. Teksty w `specs.jsonl.gz`. |

**Proponowany eksperyment.** Wytrenować detektor na MaliciousSkillBench. Dla ręcznie sprawdzonych speców ze SpecMine przygotować pary różniące się jednym wymaganiem, np. dodaniem zapisu tokenu do logów. Zmierzyć, jak często detektor oznacza zmieniony spec jako szkodliwy, a oryginał jako bezpieczny.
