#!/usr/bin/env python3
import os
import sys
import requests
import json
from datetime import datetime
from github import Github
import time

def fetch_citybike_data(api_url, output_path):
    """Fetch data from the CityBike API and save to a file."""
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        
        # Save the raw data
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"Successfully downloaded data to {output_path}")
        return True
    except Exception as e:
        print(f"Error downloading data: {e}")
        return False

def create_branch_and_pr(github_token, repo_name, file_path):
    """Create a new branch, commit changes, and create a PR with auto-merge enabled."""
    try:
        # Initialize Github client
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        # Get default branch (usually 'main')
        default_branch = repo.default_branch
        
        # Create a new branch name based on the current date/time
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_branch_name = f"data-update-{current_time}"
        
        # Get the reference to the default branch
        source_ref = repo.get_git_ref(f"heads/{default_branch}")
        source_sha = source_ref.object.sha
        
        # Create new branch
        repo.create_git_ref(f"refs/heads/{new_branch_name}", source_sha)
        print(f"Created new branch: {new_branch_name}")
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Get the file name from the path
        file_name = os.path.basename(file_path)
        
        # Check if file exists in repo to decide between create or update
        try:
            contents = repo.get_contents(file_name, ref=new_branch_name)
            repo.update_file(
                contents.path, 
                f"Update {file_name} - {current_time}", 
                content, 
                contents.sha, 
                branch=new_branch_name
            )
            print(f"Updated file {file_name} in branch {new_branch_name}")
        except Exception:
            # File doesn't exist, create it
            repo.create_file(
                file_name, 
                f"Add {file_name} - {current_time}", 
                content, 
                branch=new_branch_name
            )
            print(f"Created new file {file_name} in branch {new_branch_name}")
        
        # Create pull request
        pr = repo.create_pull(
            title=f"Update CityBike Data - {current_time}",
            body="Automatically generated PR with updated CityBike data.",
            head=new_branch_name,
            base=default_branch
        )
        print(f"Created PR #{pr.number}")
        
        # Add auto-merge label
        pr.add_to_labels("auto-merge")
        print("Added auto-merge label to PR")
        
        # Wait for CI checks to complete (optional)
        print("Waiting for CI checks to complete...")
        time.sleep(60)  # Wait for 60 seconds for CI to kick in
        
        # Enable auto-merge
        # Note: This requires branch protection rules to be set up correctly
        try:
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            merge_endpoint = f"https://api.github.com/repos/{repo_name}/pulls/{pr.number}/auto_merge"
            merge_data = {
                "merge_method": "squash"
            }
            merge_response = requests.put(merge_endpoint, headers=headers, json=merge_data)
            
            if merge_response.status_code in [200, 202]:
                print(f"Auto-merge enabled for PR #{pr.number}")
            else:
                print(f"Failed to enable auto-merge: {merge_response.status_code} - {merge_response.text}")
        except Exception as e:
            print(f"Error enabling auto-merge: {e}")
        
        return True
    except Exception as e:
        print(f"Error in GitHub operations: {e}")
        return False

def main():
    # Configuration
    github_token = os.environ.get("GITHUB_TOKEN")
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable is not set.")
        sys.exit(1)
    
    repo_name = "AdityaSreevatsaK/GetCityBikeData"
    api_url = "https://citybik.es/api/v2/networks/decobike-miami-beach"
    output_file = "miami_bike_data.json"
    
    # Fetch data
    if not fetch_citybike_data(api_url, output_file):
        sys.exit(1)
    
    # Create branch and PR
    if not create_branch_and_pr(github_token, repo_name, output_file):
        sys.exit(1)
    
    print("Process completed successfully.")

if __name__ == "__main__":
    main()
