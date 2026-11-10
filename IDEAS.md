# Pomysły badawcze na MSR Challenge 2027 - spotkanie 10 listopada 2026

Punkt wyjścia: zbiór GitSkills z [MSR Mining Challenge 2027](https://2027.msrconf.org/track/msr-2027-mining-challenge).

## 1. Detekcja nieaktualnych skilli

**Pytanie:** Czy można automatycznie wykrywać instrukcje, które przestały pasować do projektu lub używanych narzędzi?

Analiza odwołań do plików, skryptów, API i wersji zależności oraz ich zgodności z odpowiednią wersją repozytorium. Ocena na ręcznie zweryfikowanej próbie; historia zmian pozwoli odróżnić instrukcje nieaktualne od błędnych od początku. Sam wiek skilla nie świadczy o nieaktualności.

## 2. Miara uniwersalności skilla

**Pytanie:** Na ile skill nadaje się do wykorzystania w różnych projektach bez modyfikacji?

Propozycja miary uwzględniającej zależność od konkretnego projektu, technologii i lokalnego środowiska. Weryfikacja przez ocenę przydatności poza projektem źródłowym, a dla wybranych skilli także eksperymenty z agentem. Uniwersalności nie należy utożsamiać z popularnością ani ogólnikowością instrukcji.

## 3. Kompresja i redakcja skilli

**Pytanie:** Jak zmniejszyć liczbę tokenów instrukcji bez istotnego pogorszenia skuteczności agenta?

Porównanie oryginału z wersjami pozbawionymi powtórzeń, skróconymi językowo lub przekształconymi w zwięzłą procedurę. Pomiar poprawności wykonania tych samych zadań oraz całkowitego zużycia tokenów, łącznie z poprawkami. Krótsza instrukcja może bowiem prowadzić do większej liczby błędów i ponownych prób.

## 4. Zwięzły ekstrakt do wyszukiwania i wyboru skilla

**Pytanie:** Czy kilka słów kluczowych lub jedno zdanie wystarcza do trafnego dobrania skilla do zadania?

Porównanie ekstraktów różnej długości z oryginalnym opisem skilla. Ocena trafności wyboru na zestawie zadań z ręcznie ustalonymi pasującymi skillami oraz kosztu tokenowego. Ekstrakt służy do wyboru; po wyborze agent otrzymuje pełną instrukcję.

## 5. Cel i esencja skilla niezależnie od formy

**Pytanie:** Czy można rozpoznać, co skill ma osiągnąć i jakie ograniczenia musi zachować, niezależnie od stylu i układu tekstu?

Wyodrębnienie celu, warunków zastosowania i kluczowych ograniczeń. Ocena na parach instrukcji: parafrazach zachowujących znaczenie oraz podobnych tekstach różniących się istotnym wymaganiem. Potencjalne zastosowania to wykrywanie duplikatów semantycznych i kontrola, czy kompresja zachowuje sens.

## 6. Rozpoznawanie dziedziny skilla

**Pytanie:** Czy można automatycznie określić dziedziny zastosowania skilla, np. biologię, finanse lub bazy danych?

Opracowanie klasyfikacji wieloetykietowej, z możliwością oznaczenia instrukcji jako ogólnej. Warto osobno opisywać dziedzinę, rodzaj zadania i technologię: analiza danych biologicznych w Pythonie może otrzymać wszystkie trzy etykiety. Ocena na ręcznie oznaczonej próbie, obejmującej także skille z pogranicza dziedzin.

---

Pomysły 3–5 są powiązane, ale dotyczą różnych efektów: **krótszej instrukcji do wykonania**, **krótkiego opisu do wyboru** oraz **reprezentacji znaczenia**.

