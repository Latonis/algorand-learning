sudo -u algorand -E goal account changeonlinestatus --address=<address> --online=true --txfile=keyreg.txn
sudo -u algorand -E algokey sign -m "<passphrase>" -t keyreg.txn -o keyreg.txn.signed
sudo -u algorand -E goal clerk rawsend -f keyreg.txn.signed
