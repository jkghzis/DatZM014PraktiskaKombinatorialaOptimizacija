# DatZM014PraktiskaKombinatorialaOptimizacija

# main.py
Satur problēams aprakstošos objektus, kā arī risinājuma objektu un tās saistītās funkcijas, kā arī Simulated Annealing algoritma implementāciju.

# experiment.py
Satur konfigurācijas komplektus, ar kuriem tiek veikti atkārtoti eksperimenti, lai novērtētu algoritma efektivitāti.

Darbināšana.
```
python experiments.py	                    // Visi konfigurētie eksperimenti; pēc tam "benchmark".
python experiments.py all	                // Tas pats, tikai eksplicīti.
python experiments.py experiments	        // Tikai 6 konfigurācijas eksperimentus.
python experiments.py benchmarks	        // Tikai optimālā vai labāk zināmo risinājuma salīdzinājums ar SA rezultātu.
python experiments.py small_default	        // Tikai specifisku eksperimenta vairantu (default-parameter).
python experiments.py medium_cooling_095	
// etc.
```
# results
Satur eksperimentā iegūtos rezultātus.