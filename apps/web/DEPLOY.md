# Deploy to GitHub

Follow these steps to upload this HomeOps demo to your GitHub repository.

## 1. Create a new repository on GitHub

1. Go to [GitHub](https://github.com) and log in.
2. Click the "+" icon in the top right, select **New repository**.
3. Name it `homeops` (or whatever you like).
4. Choose **Public** or **Private**.
5. **Do not** initialize with README, .gitignore, or license (we already have them).
6. Click **Create repository**.

## 2. Initialize git locally (if not already)

Open a terminal in the project directory and run:

```bash
# Initialize git repository
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: HomeOps AI Home Assistant MVP"
```

## 3. Connect to your GitHub repository

```bash
# Replace YOUR-USERNAME with your GitHub username
git remote add origin https://github.com/YOUR-USERNAME/homeops.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## 4. Deploy to Vercel / Netlify (Optional)

### Vercel
1. Install Vercel CLI: `npm i -g vercel`
2. Run `vercel` and follow prompts.
3. Or connect your GitHub repo at [vercel.com](https://vercel.com).

### Netlify
1. Drag and drop the `dist` folder to [Netlify Drop](https://app.netlify.com/drop).
2. Or connect your GitHub repo at [netlify.com](https://netlify.com).

## 5. Share your live demo

Once deployed, share the live URL with your hackathon judges or investors!

---

**Quick note**: The built files are in the `dist` folder. The deployment service will automatically run `npm run build` if you connect the repository.

## 6. Updating the repository

After making changes:

```bash
git add .
git commit -m "Update: [describe changes]"
git push
```

---

**Need help?** Check out GitHub's [documentation](https://docs.github.com/en/get-started/importing-your-projects-to-github/importing-source-code-to-github/adding-existing-source-code-to-github).