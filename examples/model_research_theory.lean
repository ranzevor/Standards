namespace MRDemo

theorem successor_exists (n : Nat) : ∃ m : Nat, n < m :=
  ⟨Nat.succ n, Nat.lt_succ_self n⟩

theorem square_nonnegative (n : Nat) : 0 ≤ n * n :=
  Nat.zero_le (n * n)

#print axioms MRDemo.successor_exists
#print axioms MRDemo.square_nonnegative

end MRDemo
