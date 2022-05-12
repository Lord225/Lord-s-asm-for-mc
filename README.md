# Lord-s-asm-for-mc
Program kompilujący całkowicie customowy assembler, przyjmując schemat komend w pliku `json`

## Możliwości
### Syntax
Program daje dużo swobody w formie i wyglądzie komend.
Przykładowo można określić dowolną składnie, nawet specyficzną dla danej architektury
```
mov 1, reg[1]
add reg[1], reg[2], reg[3]
```
```
reg[1] = 1
ram[reg[2]] = reg[1] 
```
```
if r1 > r2 jump to LABEL
```
```
AD2 MOV MC1, X MOV MUL, P MOV MC0, Y CLR A      MOV ALH, MC3
AD2 MOV MC1, X MOV MUL, P MOV MC0, Y MOV ALU, A MOV #0, CT1
```
```
loop:
    move.b (a1), (a0)
    add.l #1, a0
    add.l #1, a1
    abra d1, loop
```

### Preprocesor
Kompilaor posiada podstawowy preprocesor, insporowany tym z C. Obsługuje `#define`, `#ifdef`.
Posiada swoje makra i możliwość dodawania symboli debugowania dla emulatora.

### Emulator
Kompilator można zlinkować z emulatorem, aby automatycznie wpisywał i wykonywał podany program. Posiada podstawowe narzędzia do debugowania. 
* `disassembly` - wyświetla dezasemblacja 
* `#debug` - Pozwala dodawać symbole do debugowania które są interpretowane przez kompilator
  * `#debug ram` - Wyświetla zawartość rejestrów gdy trafi na ten symbol
  * `#debug break` - Zatrzymuje emulator gdy trafi na ten symbol
  * Dowolne customowe symbole w emulatorze. 

## Przykłady
Prawdopodobnie będziesz chciał to uruchomić w jeden z następujących sposobów:

Uruchom i zapisz.
```
python compile.py --run --comments --save pad 
```
Zapisz jako schematic (Jeżeli dostępne)
```
python compile.py --save schem 
```
Uruchom ze wszystkimi narzędziami do debugowwania
```
python compile.py --run --logs
```
Skompiluj inny plik niż domyślny, zapisz z inną nazwą
```
python compile.py -i src/nazwa_pliku.lor -o compiled/output.txt --save pad
```
Zapisz jako json
```
python compile.py --save py
```
Przekierowanie outputu do pliku (wyłącz breakpointy)
```
python compile.py --run --logs > output.txt
```
## ArgParser
### -i --input
Ścieżka pliku wejściowego z programem, 
Domyślnie src/program.lor
### -o --output
Ściezka pliku wyjściowego. Do nazwy zostanie dodana nazwa entrypoint'a.


Domyślnie: compiled/compiled.txt
### -s --save
format z jakim ma zostać zapisana binarka.
* `raw` - argumenty podane hexadecymalnie w bajtach
* `bin` - argumenty w systemie binarnym, wyrównane do argumentów
* `pad` - argumenty w systemie binarnym, wyrównane do bajta
* `py`  - zapisuje w postaci json'a
* `schem` - zapisuje w postaci schematica


Domyślnie: None (Nie wykona zapisu)
### -c --comments
Jeżeli plik ma zostać zapisany, czy na końcu każdej linijki mają być załączone komentarze z liniami w assemblerze, etykietami i fizycznymi adresami komend.
### -r --run
Uruchom emulacje
### --logs
Czy podczas emulacji mają się wyświetlać operacje procesora. (nie wpływa na komendy debugowania)
### --why
Kompilator bardziej się postara przy wyświetlaniu komunikatu błędu.

