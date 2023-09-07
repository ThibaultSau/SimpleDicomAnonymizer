1) Décompresser le dossier "dist" puis le déplacer dans le même dossier que celui qui contient les fichiers DICOM à anonymiser. 
Par exemple si le dossier à anonymiser est : C:\Utilisateurs\nom_utilisateur\Bureau\Etude10\DICOMS, alors déplacer "dist"
dans C:\Utilisateurs\nom_utilisateur\Bureau\Etude10.

2) Compléter le fichier "folder.txt" : Dans l'exemple précédent mettre ../DICOMS.

3) Eventuellement compléter le fichier corr_names.txt pour ajouter une couche d'anonymisation. La structure est de la forme Nom;Nom_anonymisé.
Si le fichier est vide ou incomplet le programme s'exécutera sans problèmes mais les fichiers qui ne contiennent pas de nom anonymisé ne seront pas inclus dnas le dossier anonymisé.

4) Eventuellement ajouter des règles d'anonymisation dans le fichier "extra_rules.txt" sous la forme Adresse;Action;Nom_Du_Champs.
Les différentes actions supportées sont : delete, keep, keep_year, change_year, empty, replace et anonymize_name.

5) Lancer le fichier Anonymisation\Anonymisation.exe en double cliquant dessus. Une fenêtre s'ouvrira et donnera des informations sur les fichiers traités.