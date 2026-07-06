# Projekt act

# GitFlow

Es werden nur Commits auf dem `develop` Branch für die Reconcilation in betracht gezogen. Änderungen werden über feature branches entwickelt und via Merge Request in den `develop` Branch übertragen.

```mermaid
%%{init: { 'logLevel': 'debug', 'theme': 'dark' } }%%
    gitGraph
       commit
       commit
       branch feat_1
       checkout feat_1
       commit
       commit
       checkout develop
       merge feat_1
       commit
       branch feat_2
       checkout feat_2
       commit
       checkout develop
       merge feat_2
```