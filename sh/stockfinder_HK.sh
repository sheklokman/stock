cd /Users/lmshek/Documents/GitHubExternal/stock
if [ ! -f .env ]
then
  export $(cat .env | xargs)
fi

cd /Users/lmshek/Documents/GitHubExternal/stock & /usr/bin/env /Users/lmshek/opt/anaconda3/envs/testing/bin/python stockfinder_technical_breakout.py --market HK --stock_list forex hsi_integrated_large hsi_integrated_medium hsi_integrated_small