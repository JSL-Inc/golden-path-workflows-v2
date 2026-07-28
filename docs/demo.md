# Demonstration flow

1. Push `develop-s34`; delivery runs CI without deployment.
2. Merge `develop-s34` into `feature-eint1-f26`; that feature-branch update
   triggers one delivery run which validates and deploys to `eint1`.
3. Open a PR from the feature branch to `release-eqa-demo` or
   `release-epreprod-demo`; the required PR workflow runs CI and stage
   validation.
4. Merge the PR; GitHub creates immutable tag `f26`, then the release branch is
   built and deployed to the environment named in the branch.
5. Open the release PR to the configured production branch; the required
   workflow verifies the existing successful EQA or ePreProd deployment instead
   of redeploying it.
6. Merge; the approved artifact is promoted to `prod`, smoke tested, production
   verified, tagged as `v0.0.<delivery-run-number>`, and published as a GitHub
   Release. No release label is required.
