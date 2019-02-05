echo "gestione_risorse_umane gestione_risorse_umane/dumps/posizioni_economiche.json"
./manage.py loaddata --app gestione_risorse_umane gestione_risorse_umane/dumps/posizioni_economiche.json 

echo "gestione_risorse_umane/dumps/tipo_contratto.json"
./manage.py loaddata --app gestione_risorse_umane gestione_risorse_umane/dumps/tipo_contratto.json

echo "gestione_risorse_umane/dumps/tipo_invalidita.json"
./manage.py loaddata --app gestione_risorse_umane gestione_risorse_umane/dumps/tipo_invalidita.json
# ./manage.py loaddata --app gestione_risorse_umane gestione_risorse_umane/dumps/tipo_profilo_professionale.json

echo "gestione_peo/dumps/gestione_peo.json"
./manage.py loaddata --app gestione_peo  gestione_peo/dumps/gestione_peo.json

# ./manage.py loaddata --app unical_strutture  unical_strutture/dumps/tipo_struttura.json
# ./manage.py loaddata --app unical_strutture  unical_strutture/dumps/funzionelocazionestruttura.json
# ./manage.py loaddata --app unical_strutture  unical_strutture/dumps/strutture.json

./manage.py createsuperuser
