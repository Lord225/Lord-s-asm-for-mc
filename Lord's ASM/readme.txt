Budowa programu:
```
[] //Ustawienia (można nadpisać te z argparsera (main.py --help))
:CORE0 //Definicja programu dla rdzenia
    //stuff
    :znacznik_dla_skoku2
    //stuff
:CORE1
    //stuff
    :znacznik_dla_skoku
    //stuff
    
```

FORMAT KOMENDY

nazwa arg1, arg2, arg3

Argumenty podajesz po przecinku, każda linijka to jedna komenda

FORMAT ARGUMENTÓW

Dostęp do rejestrów:
> Sama liczba:              0           //Rejestr 0
> Fancy:                    reg[0]      //Rejestr 0

Stałe:
> Liczba z dolarem:         $0          //Wartość 0

Dostęp do ramu:
> Przez komendy (niżej)
> Fancy direct:             ram[0]      //Wartość komórki ramu o numerze 0
> Fancy indirect            ram[reg[0]] //Wartość komórki ramu o numerze z rejestru 0 (pointer)

Liczby można podawać dziesiętnie, binarnie lub szesnastkowo
DEC: 255
HEX: 0xFF
BIN: 0b11111111

TYPY ARGUMENTÓW:

KILKA PODSTAWOWYCH KOMEND:

mov from, to    //Operacje na rejestrach/pamięci
write from, to  //Wpis do pamieci (from - skąd odczytać, to do której komórki ram wpisać)
read from, to   //Odczyt z pamięci (from - z której komórki ram odczytwać, gdzie wpisać)

PRZYKŁADY:
Każdy przykład jest interpretowany w taki sam sposób (inny zapis)

//Wpis liczby 1 do rejestru 8
mov $1, 8
mov $1, reg[8]

//Kopiowanie rejestru 2 do rejestru 3
mov reg[2], reg[3]
mov 2, 3

//Wpis do komórki ram 7 wartości 2
mov $2, ram[0b111]
write $2, $0b111

//Wpis do komórki ram 3 wartości z rejestru 9
mov 9, ram[3]
write $9, $3

//Wpis przez wskaźnik z rejestru 15 liczby 0
mov $0, ram[reg[15]]
write $0, reg[0]
write $0, 0 

//Wpisz przez wskaźnik z rejestru 12 liczbę z rejestru 1
mov 1, ram[reg[12]]
mov reg[1], ram[reg[12]]
write reg[1], reg[12]
write 1, 12

//Wpisz do rejestru 1 liczbę z komórki ram 2
mov ram[2], reg[1]
mov ram[2], 1
read $2, reg[1]
read $2, 1

//Wpisz do rejestru 1 liczbę ze wskaźnika w rejestrze 3
mov ram[reg[3]], reg[1]
mov ram[reg[3]], 1
read reg[3], reg[1]
read 3, 1

ALU

add from_a, from_b, to //dodawanie     (alu 2 arg)
inc from_to            //inkrementacja (alu 1 arg)

//Dodaj 10 do rejestru 3, wpisz do rejestru 3
add $10, reg[3], reg[3]
add $10, 3, 3

//Dodaj 1 do rejestru 1, wpisz do rejestru 2
add $1, reg[1], reg[2]
add $1, 1, 2

//Zwiększ rejestr 5 o 1
add $1, reg[5], reg[5]
add $1, 5, 5
inc reg[5]              //Ładniej niż z add
inc 5

SKOKI BEZWARUNKOWE:

Po zdefiniowaniu znacznika dla skoku można się do niego odwołać w instrukcji skoku:
Po kompilacji znaczniki zostaną zamienione na odpowiednie adresu ROM

jmp adress  //Skocz do adresu adress
call adress //Wywołaj adres adress

```
:CORE0 //Wykonaj na rdzeniu 1
    :SKOCZ_TU
    //Stuff w pętli
    jmp SKOCZ_TU
:CORE1
```

//error - nie można definować dwa razy tego samego znacznika!
```
:CORE0 //Wykonaj na rdzeniu 1
    :SKOCZ_TU
    //Stuff w pętli
    jmp SKOCZ_TU

    :SKOCZ_TU
:CORE1
```

//error - to samo na dwóch rdzeniach.
```
:CORE0 //Wykonaj na rdzeniu 1
    :SKOCZ_TU
    //Stuff w pętli
:CORE1
    :SKOCZ_TU
    //Stuff w pętli
    jmp SKOCZ_TU
```

//error - tak się nie robi, kiedyś to naprawię
```
:CORE0 //Wykonaj na rdzeniu 1
    :SKOCZ_TU
    //Stuff w pętli
:CORE1
    jmp SKOCZ_TU
```

SKOKI WARUNKOWE

je from_a, from_b, adress //skocz do adresu adress jeżeli from_a == from_b
calle from_a, from_b, adress //wywołaj adres adress jeżeli from_a == from_b
jo from_a, from_b, adress //Skocz do adress jeżeli overflow jest równy 1, dla tych instrukcji from_a, from_b jest nieużywane

PRZYKŁAD:

//Skocz jeżeli reg[1] == reg[2]
je reg[1], reg[2], SKOCZ_TU
je 1, 2, SKOCZ_TU

//Skocz jeżeli reg[2] == 1
je $1, reg[2], SKOCZ_TU
je $1, 2


Wszystkie komendy i dekoratory:
//"$" = value
//" " = depends on cmd - reg adress or 
mov $from, to
mov from, to
or A, B, to
or $A, B, to
and A, B, to
and $A, B, to
xor A, B, to
xor $A, B, to
rsh A, B, to
rsh $A, B, to
lsh A, B, to
lsh $A, B, to
add A, B, to
add $A, B, to
sub A, B, to
sub $A, B, to
rsub A, B, to
rsub $A, B, to
inc A
dec A
just A
not A
max A, B, to
max $A, B, to
jmp address
je A, B, address
je $A, B, address
jne A, B, address 
jne $A, B, address
jg A, B, address 
jg $A, B, address
jl A, B, address 
jl $A, B, address
jge A, B, address 
jge $A, B, address
jle A, B, address 
jle $A, B, address
jo A, B, address 
jo $A, B, address 
js A, B, address 
js $A, B, address
jz A, B, address 
jz $A, B, address
jpr A, B, address 
jpr $A, B, address
calle A, B, address 
calle $A, B, address
callne A, B, address 
callne $A, B, address
callg A, B, address 
callg $A, B, address
calll A, B, address 
calll $A, B, address
callge A, B, address 
callge $A, B, address
callle A, B, address 
callle $A, B, address
callo A, B, address 
callo $A, B, address 
calls A, B, address 
calls $A, B, address
callz A, B, address 
callz $A, B, address
callpr A, B, address 
callpr $A, B, address
call adress
int type, num
int type, $num
write from, to
read from, to
write $from, to
read $from, to
write from, $to
write $from, $to
ret


KOMENTARZE:

//To jest komentarz.

DEBUGOWANIE:

#regs     - Wyświetla rejestry w fromacie Core{} regs = [reg0 reg1 reg2 reg3 ...]
#break    - Przerywanie
#ram      - Wyświetla wszystkie komórki ram
#ramslice[a:b] - Wyświetla komórki ram od a do b
#log ____ - Wyświetla customowy log, zastąpi wszystkie znaczniki odpowiednimi wartościami:

Możliwe wartości:
{regs}
{rom_stack}
{rom_stack_len}
{stack}
{stack_len}
{flags}
{rom}
{overflow}
{sign}
{zero}
{partity}
Przykład:
    
#log customowy log wyświetlający rejestry: regs={regs} (i długość stosu!) {stack_len}
    ^
    Warunek jest taki że po #log musi być odstęp.
Wyświetli:
customowy log wyświetlający rejestry: regs=[ 0 0 0  0  0  0  0  0  0  0  0  0  0  0  0  0] (i długość stosu!) 0


STAŁE

definicja stałej:

const nazwa_stalej wartosc

Wszystkie stałe w pliku w procesie budowania zostaną zastąpione odpowiednimi wartościami
przykład


```
const ADRES_SUMY_Z_CORE1 65
const log_macro #log Tutaj jest bardzo długi log który by syfił w pliku: {regs}
:core0
    //do stuff
    int 5 // Czekaj na 2 rdzeń (składnia lordosa)
    mov reg[1], ram[ADRES_SUMY_Z_CORE1] //Odbierz wynik
    log_macro
:core1
    //do expencive stuff

    mov ram[ADRES_SUMY_Z_CORE1], reg[1]
    int 6 // Zgłoś gotowość
```


DEFINICJE

Definicje pozwalają na wyłączanie części kodu na etapie wczytywania:

BUDOWA:

#ifdef NAZWA_STALEJ
    //Stuff jeżeli zediniowane
#else
    //Stuff jeżeli nie
#endif

PRZYKŁAD:
```
[SPEED 10]

const log_macro #log fib: {regs}
//const SLOW_FIB

:CORE0
		mov $0x1, reg[1]
		mov $0x1, reg[2]
#ifdef SLOW_FIB
		mov $0x0, reg[3]
		:znacznik
		mov reg[1], reg[3]
		add reg[1], reg[2], reg[1]
		mov reg[3], reg[2]
		log_macro
		jge $144, reg[1], znacznik //if 144 >= reg[1] jump znacznik
#else
		:znacznik
		add reg[1], reg[2], reg[1]
		log_macro
		add reg[1], reg[2], reg[2]
		jge $144, reg[1], znacznik 
#endif
```








PROFILE:

"CPU":{
        "Name": "ZCore 8bit", <==== NAZWA PROCESORA
        "Architecture": "ZCore",  <==== ARCHITEKTURA
        "Author": "Zbagier",  <==== Autor
        "emulator":"zcore_emulator",  <==== Nazwa pliku z emulatorem (pythonowe gówno)
        
        "ARGUMENTS":{  <==== Argumenty w ROM (Z rozmiarem)
            "Arg":{
                "size":8
            },
            "Warunek":{
                "size":5
            },
            "NegAlu":{
                "size":1
            },
            "opALU":{
                "size":4
            },
            "readA":{
                "size":3
            },
            "readB":{
                "size":3
            },
            "write":{
                "size":3
            },
            "opCPU":{
                "size":5
            },
            "opFlow":{
                
            },
            "Interupt":{
                "size":4
            },
            "Adress":{
                "size":8
            }
        },
        "DEFINES":[ <======= komilator dołączy te definicje przy budowaniu (pozwala np korzystc ze sztuczek na danej platformie ect)
            "__ZCORE__"
        ],

        "parametrs":{ <= parametry Procesora 
            "word len":8, <=== Bitowość
            "max value": 255, <==== maksymalna wartosc słowa
            "num of regs":7, <===== ilość rejestrów

            "ram adress space":{ <====== Adresy ramu (min i max)
                "min":0,
                "max":255
            },
            "rom adress space":{ <==== adresy romu (może zaczynać się od 1 np)
                "min":0,
                "max":255
            },
            "rom stack size":16, 
            "cpu stack size":16,
            "cores":2,
            "arguments sizes":{ <====== rozmary argumentów (w dla kompilatora nie dla procesora)
                "const":255,
                "reg":7,
                "ram":255,
                "ptr":7,
                "adress":255
            },
            "SUPPORTED TECHNOLOGIES":[
                "",
                ""
            ]
        },
        "COMMANDS"{
            //DEFINICJE KOMEND
        }
}


SPOSÓB DEFINIOWANIA KOMEND:

"mov const reg":{ <======== Wyjątkowa nazwa (bez znaczenia)
    "name":"mov", <======== nazwa komendy (pierwszy czlon przy pisaniu, może się powtarzać)
    "type":"mov", <========= typ komendy (patrz niżej)
    "subtype":"mov", <======== podtyp (patrz niżej)
    "emulator":"mov_const_reg", <===== link do emulatora 
    
    (Wejdz w plik zcore_emulator w klasie Core jest pierdyliard funkcji odpowiadające różnym operacją procesora. musisz podać tutaj nazwę)
    
    
    
    "description":"Write const to register", 
    "example":"mov {}, reg[{}]", <======== podaj przykład pisania (zamiast liczb napisz {})

    "numofargs":2, <==== ilość argumentów
    "args":[ <=========== argumenty (w kolejności od lewej do prawej)
        {
            "type":"const", <======= typ argumentu: dostępne: const - stała z romu, 
            "name":"value" <======== NAZWA argumentu (musi byc wyjatkowa w komendzie), potem podajesz przy bin
        },
        {
            "type":"reg",
            "name":"to"
        }
    ],
    "bin":{
        "arg":"value", <======= podajesz argument w rom (sekcja wyżej, ARGUMENTS) i dajesz liczbe/nazwe argumentu.
        "write":"reg",
        "opCPU":1      <==== stała dla danego argumentu
    }
},