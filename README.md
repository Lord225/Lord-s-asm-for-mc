# Lord-s-asm-for-mc
Na wiki opisana jest składnia.
## Przykłady
Prawdopodobnie będziesz chciał to uruchomić w jeden z następujących sposobów:


Uruchom i zapisz.
```
python compile.py --run --comments --save bin 
```
Uruchom ze wszystkimi narzędziami do debugowwania
```
python compile.py --run --logs
```
Skompiluj inny plik niż domyślny, zapisz z inną nazwą
```
python compile.py --file src/nazwa_pliku.lor --outfile compiled/output.txt --save bin
```
Zapisz jako pythonowy dict
```
python compile.py --save py
```
## ArgParser
### -i --input
Nazwa pliku z programem, 
Domyślnie src/program.lor
### -o --output
Nazwa pliku wynikowego. Jeżeli ma zostać zapisane w wielu plikach, na końcu zostanie dołączona informacja z którego rdzenia jest to kod na przykład `compiled_CORE0.txt` zamiast `compiled.txt`
Domyślnie: compiled/compiled.txt
### -s --save
format z jakim ma zostać zapisana binarka.
* dec - argumenty zarówno w systemie dziesiętnym jak i dwójkowym
* raw - argumenty podane hexadecymalnie w bajtach
* bin - argumenty w systemie binarnym, wyrównane do argumentów
* pad - argumenty w systemie binarnym, wyrównane do bajta
* py  - surowy zapis pythona
Domyślnie: None (Nie wykona zapisu)
### -c --comments
Jeżeli plik ma zostać zapisany, czy na końcu każdej linijki mają być załączone komentarze z komendami assemblera.
Na przykład:
```0000 0000 0000 0000 | mov 0, reg[0]```
Domyślnie: false
### -r --run
Czy program ma zostać zemulowany
### --logs
Czy emulator ma pokazywać w konsoli wszystkie komendy i skoki.
Domyślnie: false
