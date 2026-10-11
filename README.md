# DatZM014PraktiskaKombinatorialaOptimizacija

Darbu veidoja je21033.

# main.py
Satur problēams aprakstošos objektus, kā arī risinājuma objektu un tās saistītās funkcijas, kā arī Simulated Annealing algoritma implementāciju.

# experiments.py
Satur konfigurācijas komplektus, ar kuriem var atkārtoti veikt eksperimentus, lai novērtētu algoritma efektivitāti.

Darbināšana:
```
python experiments.py	                    // Visi konfigurētie eksperimenti; pēc tam "benchmark".
python experiments.py all	                // Tas pats, tikai eksplicīti.
python experiments.py experiments	        // Tikai 6 konfigurācijas eksperimentus.
python experiments.py benchmarks	        // Tikai optimālā vai labāk zināmo risinājuma salīdzinājums ar SA rezultātu.
python experiments.py small_default	        // Tikai specifisku eksperimenta vairantu (default-parameter).
python experiments.py medium_cooling_095	// ...
// etc.
```
# *results
Satur eksperimentā iegūtos rezultātus. No šiem datiem ir iespējams arī veidot vizualizācijas, kas darba laikā netika izstrādāta.

Piezīme: benchmark csv satur kolonnu optimality_gap_percent, kas netika līdz galam izstrādāta. 