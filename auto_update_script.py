#!/usr/bin/env python3
import os
import sys
import requests
import json
from datetime import datetime
import pytz
from github import Github
import time

def fetch_citybike_data(api_url, output_folder, output_file):
    """Fetch data from the CityBike API and save to a file."""
    try:
        # Create folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Full path for the output file
        output_path = os.path.join(output_folder, output_file)
        
        response = requests.get(api_url)
        response.raise_for_status()
        
        # Save the raw data
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"Successfully downloaded data to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None

def create_branch_and_pr(github_token, repo_name, file_path, folder_path):
    """Create a new branch, commit changes, and create a PR with auto-merge enabled."""
    try:
        # Initialize Github client
        g = Github(github_token)
        repo = g.get_repo(repo_name)
        
        # Get default branch (usually 'main')
        default_branch = repo.default_branch
        
        # Create a new branch name based on the current date/time in NY timezone
        ny_tz = pytz.timezone('America/New_York')
        current_time = datetime.now(ny_tz).strftime("%Y%m%d_%H%M%S")
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
        
        # Get the folder name and file name from the paths
        repo_folder_path = os.path.basename(folder_path)
        file_name = os.path.basename(file_path)
        repo_file_path = f"{repo_folder_path}/{file_name}"
        
        # Check if folder exists in repo
        try:
            repo.get_contents(repo_folder_path, ref=new_branch_name)
            print(f"Folder {repo_folder_path} exists")
        except Exception:
            # Create an empty file to ensure folder exists
            repo.create_file(
                f"{repo_folder_path}/.gitkeep", 
                f"Create folder {repo_folder_path}", 
                "", 
                branch=new_branch_name
            )
            print(f"Created folder {repo_folder_path}")
        
        # Check if file exists in repo to decide between create or update
        try:
            contents = repo.get_contents(repo_file_path, ref=new_branch_name)
            repo.update_file(
                contents.path, 
                f"Update {file_name} - {current_time}", 
                content, 
                contents.sha, 
                branch=new_branch_name
            )
            print(f"Updated file {repo_file_path} in branch {new_branch_name}")
        except Exception:
            # File doesn't exist, create it
            repo.create_file(
                repo_file_path, 
                f"Add {file_name} - {current_time}", 
                content, 
                branch=new_branch_name
            )
            print(f"Created new file {repo_file_path} in branch {new_branch_name}")
        
        # Create pull request
        pr = repo.create_pull(
            title=f"Update CitiBike Data - {current_time}",
            body=f"Automatically generated PR with updated CitiBike data for {repo_folder_path}/{file_name}.",
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
    api_url = "https://gbfs.citibikenyc.com/gbfs/en/station_status.json"
    
    # Get current date and time in New York timezone
    ny_tz = pytz.timezone('America/New_York')
    now = datetime.now(ny_tz)
    
    # Create folder name based on date (YYYY-MM-DD)
    folder_name = now.strftime("%Y-%m-%d")
    
    # Create file name with date and time (YYYY-MM-DD_HH-MM-SS)
    file_name = f"Station-Status_{now.strftime('%Y-%m-%d_%H-%M-%S')}.json"
    
    # Create local folder for the day if it doesn't exist
    local_folder_path = os.path.join(os.getcwd(), folder_name)
    
    # Fetch data
    file_path = fetch_citybike_data(api_url, local_folder_path, file_name)
    if not file_path:
        sys.exit(1)
    
    # Create branch and PR
    if not create_branch_and_pr(github_token, repo_name, file_path, folder_name):
        sys.exit(1)
    
    print("Process completed successfully.")

if __name__ == "__main__":
    main()
