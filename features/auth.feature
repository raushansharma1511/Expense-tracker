Feature: User Authentication

  Scenario Outline: User registration
    When a user registers with the username "<username>", email "<email>", password "<password>", and name "<name>"
    Then the response status code should be <status_code>
    And the response should contain fields: <expected_fields>

    Examples:
        | username  | email                | password      | name      | status_code | expected_fields           |
        | newuser1  | newuser1@example.com | Password123!  | New User  | 201         | id,username,email,name    |
        | newuser1  | invalid_email        | short         | New User  | 400         | error                          |


  Scenario Outline: User login
    Given a user is registered with username "<username>" and password "testpassword12@"
    When the user logs in with username "<login_username>" and password "<login_password>"
    Then the response status code should be <status_code>
    And the response should contain fields: <expected_fields>

    Examples:
      | username  | login_username | login_password   | status_code | expected_fields            |
      | testuser  | testuser       | testpassword12@  | 200         | access_token,refresh_token |
      | testuser  | testuser       | wrongpass        | 400         | error                          |

  @authenticated
  Scenario: User logout
    When the user sends a POST request to "/api/auth/logout/"
    Then the response status code should be 200
