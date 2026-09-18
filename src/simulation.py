"""
Dark Store Dispatch Simulation - Phase 1
------------------------------------------
Models orders arriving randomly at a dark store and being delivered by a
limited pool of riders. Measures average delivery time, SLA breach rate,
and rider utilization.

Phase 2 (later): add order batching (a rider carrying 2 orders per trip).
"""

import simpy
import random
import pandas as pd

# ---------------------------
# CONFIG - tweak these to run different scenarios
# ---------------------------
RANDOM_SEED = 42
SIM_TIME = 8 * 60          # simulate an 8-hour shift, in minutes
AVG_ORDER_INTERVAL = 2     # avg minutes between order arrivals
NUM_RIDERS = 8              # <-- change this between runs (e.g. 5 vs 8)
PICKUP_TIME = 2             # minutes to pack/hand over an order
DELIVERY_TIME_MEAN = 12     # avg minutes to deliver once rider leaves store
SLA_MINUTES = 20            # order must be delivered within this to count as "on time"


class DarkStore:
    def __init__(self, env, num_riders):
        self.env = env
        self.riders = simpy.Resource(env, num_riders)
        self.records = []  # store per-order results here

    def deliver_order(self, order_id, order_placed_time):
        """Simulates one rider handling one order, start to finish."""
        with self.riders.request() as request:
            yield request  # wait until a rider is free

            wait_for_rider = self.env.now - order_placed_time

            # pack the order
            yield self.env.timeout(PICKUP_TIME)

            # deliver it (randomized delivery time)
            delivery_duration = random.expovariate(1.0 / DELIVERY_TIME_MEAN)
            yield self.env.timeout(delivery_duration)

            total_time = self.env.now - order_placed_time
            met_sla = total_time <= SLA_MINUTES

            self.records.append({
                "order_id": order_id,
                "wait_for_rider": wait_for_rider,
                "total_delivery_time": total_time,
                "met_sla": met_sla,
            })


def order_generator(env, store):
    """Creates new orders arriving at random intervals."""
    order_id = 0
    while True:
        yield env.timeout(random.expovariate(1.0 / AVG_ORDER_INTERVAL))
        order_id += 1
        env.process(store.deliver_order(order_id, env.now))


def run_simulation(num_riders):
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    store = DarkStore(env, num_riders)
    env.process(order_generator(env, store))
    env.run(until=SIM_TIME)
    return pd.DataFrame(store.records)


if __name__ == "__main__":
    results = run_simulation(NUM_RIDERS)

    print(f"--- Results with {NUM_RIDERS} riders ---")
    print(f"Orders completed: {len(results)}")
    print(f"Avg delivery time: {results['total_delivery_time'].mean():.2f} min")
    print(f"Avg wait for rider: {results['wait_for_rider'].mean():.2f} min")
    print(f"SLA met rate: {results['met_sla'].mean() * 100:.1f}%")

    # save raw results for later comparison / plotting
    results.to_csv(f"results_{NUM_RIDERS}_riders.csv", index=False)