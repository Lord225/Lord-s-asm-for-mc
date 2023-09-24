# Lord-s-asm-for-mc
Program kompilujący całkowicie customowy assembler, przyjmując schemat komend w pliku `json`

# Instalacja
* Sklonuj repo lub pobierz jako zip i wypakuj
* Uruchom `setup.ps1` w powershellu lub `setup.sh` w bash'u
  * skrypt doda alias do kompilatora nazwany `lor`. Możesz teraz otworzyć dowolny folder i wpisać `lor` aby używać kompilatora
  * skrypt doda również komende sendrf. Pozwala wysyłać schematici na redstonefun.pl
  * skrypt doda folder do PATH
  * skrypt modyfikuje profil powershella. Możesz go zobaczyć wpisując `code $profile` 
* Możesz cofnąć zmiany uruchamając skrypt `revert`

## Możliwości
### Syntax
Program daje dużo swobody w formie i wyglądzie komend.
Kilka przykładowych składni które są do uzyskania przy użyciu tego programu

Proste argumenty oddzielane przecinkami
```
mov 1, reg[1]
add reg[1], reg[2], reg[3]
```
Zapis "Matematyczny"
```
reg[1] = 1
ram[reg[2]] = reg[1] 
```
Opis symbolami
```
if r1 > r2 jump to LABEL
```
DSP's (Wielopotokowy, bardzo specyficzny assembler)
```
AD2 MOV MC1, X MOV MUL, P MOV MC0, Y CLR A      MOV ALH, MC3
AD2 MOV MC1, X MOV MUL, P MOV MC0, Y MOV ALU, A MOV #0, CT1
```
Sega Mega Drive
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
### Makra
Kompilator pozwala na definiowanie proceduralnych makr, które wyglądają jak komendy. Pozwala to rozwinąć jedno makro  na wiele komend.
```
jne reg[1], reg[2], JUMP          // Marka pozwalają dodać abstrakcję do powtarzalnego kodu
mov reg[1], ram[reg[2] + 2]       // Makra można skryptować z użyciem pythona aby generować bardzo specyficzny, ogólny kod
rsh reg[2], 3                     // Makra mogą wywoływać się rekurencyjne
```
```
// jne reg[1], reg[2], JUMP
cmp reg[1], reg[2]     // Wykonało podstawienie
jz JUMP

// mov reg[1], ram[reg[2] + 2]
push reg[3]    // Skrypt w pythonie wybrał rejestr 3 bo to pierwsza wartość różna od 0, 1, 2
add reg[3], reg[2], 2
mov reg[1], ram[reg[3]]
pop reg[3]

// rsh reg[2], 3
rsh reg[2] // Maro rozwineło się trzy razy, za każdym razem podstawiając siebie z innymi parametrami 
rsh reg[2]
rsh reg[2]
```
## Przykłady
Prawdopodobnie będziesz chciał to uruchomić w jeden z następujących sposobów:

### Zapisz
Skompiluj i zapisz. (plik domylśny to `program.lor`)
```
lor -s pad -c 
```
Zapisz jako schematic
```
lor compile.py -s schem 
```
Wgraj schematic na serwer
```
lor | rfsend --nick NICK --pass PASS -c
```
### Emuluj
Uruchom emulator z logami
```
lor --run --logs
```
Skompiluj inny plik niż domyślny, zapisz z inną nazwą
```
lor -i src/nazwa_pliku.lor -o compiled/output.txt --save pad
```
Zapisz jako json
```
lor --save py
```

### Twórz
Sprawdź jakie profile są zainstalowane (folder `profiles`)
```
lor --installed
```

Zainstaluj profil z repo na githubie (wymagany `git`)
```
lor --install <GIT LINK>
```

Stwórz własny profil!
```
lor --new-profile my-cpu
```

Stwórz własny profil, zapisz odrazu w głównym folderze
```
lor --new-profile my-cpu --home
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
* `hex` - argumenty podane hexadecymalnie w bajtach
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

