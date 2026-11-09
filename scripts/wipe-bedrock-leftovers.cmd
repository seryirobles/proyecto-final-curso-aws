@echo off
rem Deletes the personal-account Bedrock resources declared in terraform/bedrock.tf,
rem so a fresh state can recreate them without name clashes. Only touches
rem %NAME%-* resources. Usage: scripts\wipe-bedrock-leftovers.cmd [/yes]
setlocal

if not defined PROFILE set "PROFILE=personal-srobles"
if not defined NAME set "NAME=lab-final-srobles-dev"

set "A="
for /f "delims=" %%i in ('aws sts get-caller-identity --profile %PROFILE% --query Account --output text 2^>nul') do set "A=%%i"
if not defined A (
  echo Not logged in to profile %PROFILE%: run aws login --profile %PROFILE%
  exit /b 1
)

set "U=%NAME%-bedrock-invoker"
set "KS=arn:aws:iam::%A%:policy/%NAME%-ai-kill-switch"

echo Account %A% profile %PROFILE%: will delete user %U%, role %NAME%-budget-action,
echo policy %NAME%-ai-kill-switch, budget %NAME%-ai and its action.
if /i not "%~1"=="/yes" (
  set "ANS="
  set /p "ANS=Type the account id to confirm: "
  if not "%ANS%"=="%A%" (
    echo Aborted.
    exit /b 1
  )
)

rem 1. Budget action, then budget (the action blocks deleting the role)
set "IDS="
for /f "delims=" %%l in ('aws budgets describe-budget-actions-for-budget --account-id %A% --budget-name %NAME%-ai --profile %PROFILE% --query "Actions[].ActionId" --output text 2^>nul') do set "IDS=%%l"
if defined IDS for %%i in (%IDS%) do aws budgets delete-budget-action --account-id %A% --budget-name %NAME%-ai --action-id %%i --profile %PROFILE%
aws budgets delete-budget --account-id %A% --budget-name %NAME%-ai --profile %PROFILE%

rem 2. The user: API keys, kill-switch attachment, inline policy, then the user
set "KEYS="
for /f "delims=" %%l in ('aws iam list-service-specific-credentials --user-name %U% --profile %PROFILE% --query "ServiceSpecificCredentials[].ServiceSpecificCredentialId" --output text 2^>nul') do set "KEYS=%%l"
if defined KEYS for %%k in (%KEYS%) do aws iam delete-service-specific-credential --user-name %U% --service-specific-credential-id %%k --profile %PROFILE%
aws iam detach-user-policy --user-name %U% --policy-arn %KS% --profile %PROFILE% 2>nul
aws iam delete-user-policy --user-name %U% --policy-name %NAME%-invoke-model --profile %PROFILE%
aws iam delete-user --user-name %U% --profile %PROFILE%

rem 3. The role, then the kill-switch policy
aws iam delete-role-policy --role-name %NAME%-budget-action --policy-name %NAME%-attach-kill-switch --profile %PROFILE%
aws iam delete-role --role-name %NAME%-budget-action --profile %PROFILE%
aws iam delete-policy --policy-arn %KS% --profile %PROFILE%

echo Done.
endlocal
