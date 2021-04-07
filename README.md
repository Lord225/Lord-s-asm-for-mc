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
python compile.py --run --const DEBUG --logs
```
Skompiluj inny plik niż domylśny, zapisz z inną nazwą
```
python compile.py --file src/nazwa_pliku.lor --outfile compiled/output.txt --save bin
```
Zapisz jako pythonowy dict
```
python compile.py --save py --onefile
```
## ArgParser
### -f --file
Nazwa pliku z programem, 
Domyślnie src/program.lor
### -o --outfile
Nazwa pliku wynikowego. Jeżeli ma zostać zapisane w wielu plikach, na końcu zostanie dołączona informacja z którego rdzenia jest to kod na przykład `compiled_CORE0.txt` zamiast `compiled.txt`
Domyślnie: compiled/compiled.txt
### -s --save
format z jakim ma zostać zapisana binarka.
* dec - argumenty zarówno w systemie dziesiętnym jak i dwójkowym
* raw - argumenty w systemie binarnym, wyrównane do co czwartego bitu tzn `0000 0000 0000`
* bin - argumenty w systemie binarnym, wyrównane do argumentów
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
### -i --info
Poziom ostrzeżeń emulatora (przepełnienia, nielegalne ruchy, błędy ect)
* warnings - tylko ostrzeżenia
* errors - tylko błędy
* both - błędy i ostrzeżenia
* None - nic
Domyślnie: None
### --onerror
Akcja przy napotkaniu błędu
* interupt - Wyświetli ładny błąd i będzie czekać na input z klawiatury
* abort    - Wyświetli ładny błąd i zakończy skrypt
* None     - Wyrzuci brzydki pythonowy błąd
Domyślnie: abort
### --offset
Ustawienia ważne przy budowaniu, kompilator przesunie adresy programu o daną wartość, dzięki temu program nie musi zaczynać się od linijki 0
Dla przykładu
src/program.lor:
```
   :CORE0
0.    KOMENDA
1.    :skocz_tu
2.    KOMENDA
3.    jmp skocz_tu
4.    KOMENDA
```
compiled.txt po `python compile.py --file src/program.lor --offset 0 --onefile` 
```
   :CORE0
0.    KOMENDA
1.    KOMENDA
2.    jmp 1
3.    KOMENDA
```
compiled.txt po `python compile.py --file src/program.lor --offset 10 --onefile`
```
   :CORE0
10.    KOMENDA
11.    KOMENDA
12.    jmp 11
13.    KOMENDA
```

### --const NAZWA
Zdefiniuj stałą, zostanie ona dodana do stałych i uwzględniona przy budowaniu

### --profile
Podaj nazwę profilu procesora (pliku json) zawierającego definicje komend, link do emulatora i parametry procesora
Domyślnie "None" (Trzeba zawsze podać)
