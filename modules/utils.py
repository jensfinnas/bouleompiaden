import scipy.stats as stats

def truncated_norm_distribution(mu, sigma, lower, upper, n):
    return stats.truncnorm((lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma).rvs(n)
