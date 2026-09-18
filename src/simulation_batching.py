"""
Dark Store Dispatch Simulation - Phase 2 (Batching)
-----------------------------------------------------
Same setup as Phase 1, but riders can batch up to 2 orders per trip if a
second order arrives within a short waiting window. Compares against the
no-batching baseline at the SAME rider count.
"""

import simpy
import random
import pandas as pd

# ---------------------------
# CONFIG
# ---------------------------
RANDOM_SEED = 42
SIM_TIME = 8 * 60
AVG_ORDER_INTERVAL = 2
NUM_RIDERS = 5              # keep same as baseline for fair comparison
PICKUP_TIME = 2
DELIVERY_TIME_MEAN = 12
EXTRA_STOP_TIME = 5         # extra minutes to deliver a 2nd batched order
BATCH_WAIT = 1.5            # how long a rider waits to see if a 2nd order shows up
SLA_MINUTES = 20

ENABLE_BATCHING = False       # <-- flip this to False to compare fairly


class DarkStore:
    def __init__(self, env, num_riders):
        self.env = env
        self.order_queue = simpy.Store(env)
        self.num_riders = num_riders
        self.records = []

    def rider_process(self, rider_id):
        """A rider that repeatedly picks up (and maybe batches) orders."""
        while True:
            order1 = yield self.order_queue.get()
            wait_for_rider_1 = self.env.now - order1["placed_time"]

            batched_order = None
            if ENABLE_BATCHING:
                # wait a short window to see if a second order arrives
                get_second = self.order_queue.get()
                timeout = self.env.timeout(BATCH_WAIT)
                result = yield get_second | timeout

                if get_second in result:
                    batched_order = result[get_second]
                else:
                    # cancel the pending get so it doesn't leak into the store
                    get_second.cancel()

            # pack order 1 (and order 2 if batched)
            yield self.env.timeout(PICKUP_TIME)

            # deliver order 1
            delivery_1 = random.expovariate(1.0 / DELIVERY_TIME_MEAN)
            yield self.env.timeout(delivery_1)
            total_1 = self.env.now - order1["placed_time"]
            self.records.append({
                "order_id": order1["id"],
                "wait_for_rider": wait_for_rider_1,
                "total_delivery_time": total_1,
                "met_sla": total_1 <= SLA_MINUTES,
                "batched": batched_order is not None,
            })

            # deliver order 2, if batched (extra stop, not a full new trip)
            if batched_order is not None:
                wait_for_rider_2 = self.env.now - batched_order["placed_time"]
                yield self.env.timeout(EXTRA_STOP_TIME)
                total_2 = self.env.now - batched_order["placed_time"]
                self.records.append({
                    "order_id": batched_order["id"],
                    "wait_for_rider": wait_for_rider_2,
                    "total_delivery_time": total_2,
                    "met_sla": total_2 <= SLA_MINUTES,
                    "batched": True,
                })

    def place_order(self, order_id):
        self.order_queue.put({"id": order_id, "placed_time": self.env.now})


def order_generator(env, store):
    order_id = 0
    while True:
        yield env.timeout(random.expovariate(1.0 / AVG_ORDER_INTERVAL))
        order_id += 1
        store.place_order(order_id)


def run_simulation(num_riders):
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    store = DarkStore(env, num_riders)
    env.process(order_generator(env, store))
    for i in range(num_riders):
        env.process(store.rider_process(i))
    env.run(until=SIM_TIME)
    return pd.DataFrame(store.records)


if __name__ == "__main__":
    results = run_simulation(NUM_RIDERS)

    mode = "WITH batching" if ENABLE_BATCHING else "WITHOUT batching"
    print(f"--- Results with {NUM_RIDERS} riders ({mode}) ---")
    print(f"Orders completed: {len(results)}")
    print(f"Avg delivery time: {results['total_delivery_time'].mean():.2f} min")
    print(f"Avg wait for rider: {results['wait_for_rider'].mean():.2f} min")
    print(f"SLA met rate: {results['met_sla'].mean() * 100:.1f}%")
    if ENABLE_BATCHING:
        print(f"% of orders batched: {results['batched'].mean() * 100:.1f}%")

    suffix = "batched" if ENABLE_BATCHING else "nobatch"
    results.to_csv(f"results_{NUM_RIDERS}_riders_{suffix}.csv", index=False)