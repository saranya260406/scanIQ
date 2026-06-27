# GitHub Release Workflow

## Recommended approach
1. Keep the source code in GitHub.
2. Build the application into an installer or ZIP package on your machine.
3. Upload that package to GitHub Releases.
4. Share the Release download link with users.

## Why
- The repository stays lightweight.
- GitHub can host the source code normally.
- Large installer files are downloaded from Releases instead of being stored in the repo.

## What to upload
Upload one of these from your local machine:
- a Windows installer such as scanIQ_Setup.exe
- a packaged ZIP archive such as scanIQ_Package.zip

## Suggested release steps
1. Open your GitHub repository page.
2. Go to Releases.
3. Click Create a new release.
4. Choose a tag such as v1.0.0.
5. Add a title and short description.
6. Upload the installer or ZIP file as a release asset.
7. Publish the release.
