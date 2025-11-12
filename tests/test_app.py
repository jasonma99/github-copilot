"""Test cases for Mergington High School Activities API."""

import pytest


class TestRoot:
    """Test the root endpoint."""

    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Test the get activities endpoint."""

    def test_get_activities_success(self, client):
        """Test fetching all activities returns 200 and has expected structure."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        
        # Check that we have activities
        assert len(data) > 0
        
        # Verify all expected activities are present
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Soccer Team",
            "Basketball Club",
            "Art Club",
            "Drama Club",
            "Debate Team",
            "Math Club",
        ]
        for activity in expected_activities:
            assert activity in data

    def test_activity_structure(self, client):
        """Test that each activity has the required fields."""
        response = client.get("/activities")
        data = response.json()
        
        # Pick the first activity to check structure
        first_activity = next(iter(data.values()))
        
        assert "description" in first_activity
        assert "schedule" in first_activity
        assert "max_participants" in first_activity
        assert "participants" in first_activity
        assert isinstance(first_activity["participants"], list)

    def test_activities_have_initial_participants(self, client):
        """Test that activities have some initial participants."""
        response = client.get("/activities")
        data = response.json()
        
        # Each activity should have at least some participants
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)
            assert len(activity_data["participants"]) >= 1


class TestSignupForActivity:
    """Test the signup endpoint."""

    def test_signup_success(self, client):
        """Test successfully signing up for an activity."""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity."""
        email = "test_student@mergington.edu"
        
        # Get initial count
        response = client.get("/activities")
        initial_chess_participants = response.json()["Chess Club"]["participants"].copy()
        
        # Sign up
        client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Get updated count
        response = client.get("/activities")
        updated_participants = response.json()["Chess Club"]["participants"]
        
        assert len(updated_participants) == len(initial_chess_participants) + 1
        assert email in updated_participants

    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up with a duplicate email fails."""
        email = "duplicate_test@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            f"/activities/Chess Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity fails."""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_missing_email_param(self, client):
        """Test that signup without email parameter fails."""
        response = client.post("/activities/Chess Club/signup")
        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == 422


class TestUnregisterFromActivity:
    """Test the unregister endpoint."""

    def test_unregister_success(self, client):
        """Test successfully unregistering from an activity."""
        email = "unregister_test@mergington.edu"
        
        # First sign up
        client.post(f"/activities/Art Club/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Art Club/unregister?email={email}"
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant."""
        email = "remove_test@mergington.edu"
        
        # Sign up
        client.post(f"/activities/Drama Club/signup?email={email}")
        
        # Get count before unregister
        response = client.get("/activities")
        count_before = len(response.json()["Drama Club"]["participants"])
        assert email in response.json()["Drama Club"]["participants"]
        
        # Unregister
        client.post(f"/activities/Drama Club/unregister?email={email}")
        
        # Get count after unregister
        response = client.get("/activities")
        count_after = len(response.json()["Drama Club"]["participants"])
        assert count_after == count_before - 1
        assert email not in response.json()["Drama Club"]["participants"]

    def test_unregister_not_signed_up_fails(self, client):
        """Test that unregistering a student who is not signed up fails."""
        response = client.post(
            "/activities/Debate Team/unregister?email=not_signed_up@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from a non-existent activity fails."""
        response = client.post(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_missing_email_param(self, client):
        """Test that unregister without email parameter fails."""
        response = client.post("/activities/Chess Club/unregister")
        # FastAPI returns 422 for missing required query parameters
        assert response.status_code == 422


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_signup_and_unregister_flow(self, client):
        """Test a complete flow of signing up and then unregistering."""
        email = "integration_test@mergington.edu"
        activity = "Math Club"
        
        # Initial state: get activities
        response = client.get("/activities")
        initial_participants = response.json()[activity]["participants"].copy()
        assert email not in initial_participants
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup worked
        response = client.get("/activities")
        after_signup = response.json()[activity]["participants"]
        assert email in after_signup
        assert len(after_signup) == len(initial_participants) + 1
        
        # Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify unregister worked
        response = client.get("/activities")
        final_participants = response.json()[activity]["participants"]
        assert email not in final_participants
        assert len(final_participants) == len(initial_participants)

    def test_multiple_students_signup(self, client):
        """Test multiple students signing up for the same activity."""
        activity = "Basketball Club"
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu",
        ]
        
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()[activity]["participants"])
        
        # Sign up multiple students
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all were added
        response = client.get("/activities")
        final_count = len(response.json()[activity]["participants"])
        assert final_count == initial_count + len(emails)
        
        for email in emails:
            assert email in response.json()[activity]["participants"]

    def test_activity_name_with_spaces_and_special_chars(self, client):
        """Test that activity names with spaces are properly URL encoded."""
        # "Programming Class" has a space
        response = client.post(
            "/activities/Programming Class/signup?email=special_test@mergington.edu"
        )
        assert response.status_code == 200
