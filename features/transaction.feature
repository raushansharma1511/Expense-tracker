
Feature: Multiple Transactions

  Background:
    Given a user with a wallet and categories
  
  @authenticated_client_with_categories_and_wallet
  Scenario Outline: Perform transactions and verify wallet balance
    When the user performs a "<type>" transaction of "<amount>" with description "<description>"
    Then the transaction response status code should be 201
    And the transaction response should contain fields: id,user,wallet,amount,category,description
    And the wallet balance should be "<expected_balance>"

    Examples:
      | type   | amount | description           | expected_balance |
      | credit | 100.00 | First credit income   | 100.00           |
      | credit | 200.00 | Second credit income  | 200.00           |
      | debit  | 50.00  | First debit expense   | -50.00           |
      | debit  | 150.00 | Second debit expense  | -150.00          |
