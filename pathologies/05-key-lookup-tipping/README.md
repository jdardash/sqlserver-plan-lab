# 05. Key-lookup tipping point

**Symptom.** A query gets slower after someone adds an index that looks
obviously helpful.

**Cause.** The index seeks correctly but does not cover `Notes`, so every
qualifying row triggers a Key Lookup into the clustered index. Each lookup is a
random read. Past roughly a low single-digit percentage of the table, half a
million random reads cost more than one sequential scan.

SQL Server knows this, which is why the slow variant needs `FORCESEEK` to
reproduce it. That hint stands in for what a human does with a badly chosen
index or a well-meaning query hint.

**Fix.** Let the optimiser choose, or cover the query as in pathology 04. The
wrong fix is forcing the seek.

**Why this matters more than it looks.** "Seeks are good, scans are bad" is the
most common piece of half-learned tuning advice. Above the tipping point it is
false, and this directory is the counterexample with page counts attached: the
forced seek reads over 1.6 million pages to return the same rows the scan
returns in about 44,000.
