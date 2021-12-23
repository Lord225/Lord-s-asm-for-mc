# Lord-s-asm-for-mc
Program służący do kompilacji i emulacji customowego assemblera.
Na [wiki](../../wiki) opisana jest składnia.
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
* raw - argumenty podane hexadecymalnie w bajtach
* bin - argumenty w systemie binarnym, wyrównane do argumentów
* pad - argumenty w systemie binarnym, wyrównane do bajta
* py  - zapisuje w postaci json'a
* schem - zapisuje w postaci schematica
Domyślnie: None (Nie wykona zapisu)
### -c --comments
Jeżeli plik ma zostać zapisany, czy na końcu każdej linijki mają być załączone komentarze z liniami w assemblerze, etykietami i fizycznymi adresami komend.
### -r --run
Uruchom emulacje
### --logs
Czy podczas emulacji mają się wyświetlać operacje procesora. (nie wpływa na komendy debugowania)
### --why
Kompilator bardziej się postara przy wyświetlaniu komunikatu błędu.

