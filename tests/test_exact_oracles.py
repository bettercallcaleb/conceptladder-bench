import ast
import ipaddress
import json
import os
import re
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from conceptladder.exact import load_exact


class OracleCrossChecks(unittest.TestCase):
    def test_dns_timeline_and_bitsets(self):
        for seed in (17, 41, 91):
            for item in load_exact(seed, 4, "net-hard"):
                if not item["concept"].startswith("dns-ttl-chain") or item["level"] not in (3,4):
                    continue
                q = item["prompt"]
                m = re.search(r"at t=(\d+) in this order: (\[[^\]]+\]), with TTLs (\[[^\]]+\]) seconds\. At t=(\d+), ONLY record #(\d+) .* At t=(\d+),", q)
                self.assertIsNotNone(m, q)
                t0, names, ttls, refresh, idx, check = m.groups()
                t0,refresh,idx,check = int(t0),int(refresh),int(idx)-1,int(check)
                ttls = ast.literal_eval(ttls)
                self.assertLess(t0, refresh)
                self.assertLess(refresh, check)
                exp = [t0 + ttl for ttl in ttls]
                exp[idx] = refresh + ttls[idx]
                expected = "".join("1" if check >= t else "0" for t in exp)
                self.assertEqual(item["correct"],expected)

    def test_rbac_mask_independent(self):
        for seed in (17, 41, 91):
            for item in load_exact(seed, 4, "security-hard"):
                if not item["concept"].startswith("kubernetes-rbac-scope") or item["level"] < 2:
                    continue
                prompt = item["prompt"]
                policies = json.loads(prompt.split("Rules: ",1)[1].split(". Requests in order: ",1)[0])
                requests = json.loads(prompt.split("Requests in order: ",1)[1].split(". Return exactly ",1)[0])
                result=[]
                for req in requests:
                    allow=False
                    for rule in policies:
                        if rule["scope"]=="RoleBinding" and rule["namespace"]!=req["namespace"]:
                            continue
                        if req["group"]==rule["group"] and req["resource"] in rule["resources"] and req["verb"] in rule["verbs"]:
                            allow=True
                            break
                    result.append("1" if allow else "0")
                self.assertEqual(item["correct"],"".join(result))
                self.assertEqual(len(item["correct"]),len(requests))

    def test_scheduler_mask_independent(self):
        for seed in (17,41,91):
            for item in load_exact(seed, 4, "security-hard"):
                if not item["concept"].startswith("kubernetes-scheduling-filters"):
                    continue
                q=item["prompt"]
                selector=json.loads(q.split("Selectors=",1)[1].split(", request CPU=",1)[0])
                cpu=int(re.search(r"request CPU=(\d+)m",q).group(1))
                mem=int(re.search(r"memory=(\d+)MiB",q).group(1))
                tolerated=json.loads(q.split("exact tolerations=",1)[1].split(". Nodes in order=",1)[0])
                nodes=json.loads(q.split("Nodes in order=",1)[1].split(". Return exactly ",1)[0])
                result=[]
                for node in nodes:
                    eligible=(all(node[key]==value for key,value in selector.items()) and
                              node["free_cpu_m"]>=cpu and node["free_mem_mib"]>=mem and
                              all(t in tolerated or t.endswith(":PreferNoSchedule") for t in node["taints"]))
                    result.append("1" if eligible else "0")
                self.assertEqual(item["correct"],"".join(result))

    def test_jwt_mask_independent(self):
        for seed in (17,41,91):
            for item in load_exact(seed,4,"security-hard"):
                if not item["concept"].startswith("jwt-boundary-validation") or item["level"]<3:
                    continue
                q=item["prompt"]
                now=int(re.search(r"Current NumericDate=(\d+)",q).group(1))
                tokens=json.loads(q.split("Token claims in order: ",1)[1].split(". Return exactly ",1)[0])
                result=[]
                for token in tokens:
                    aud=token["aud"]
                    aud=aud if isinstance(aud,list) else [aud]
                    passed=(token["nbf"]<=now<token["exp"] and
                            token["iss"]=="https://issuer.example" and "payments" in aud)
                    result.append("1" if passed else "0")
                self.assertEqual(item["correct"],"".join(result))

    def test_unix_mode_actual_chmod(self):
        for seed in (17,41,91):
            for item in load_exact(seed,4,"sys-hard"):
                if not item["concept"].startswith("unix-mode-bit-transforms") or item["level"]!=4:
                    continue
                q=item["prompt"]
                m=re.search(r"umask=(0[0-7]{3}).*requested mode (0[0-7]{3}).*chmod g=u; chmod o=g; chmod ([a-z]-[rwx])",q)
                self.assertIsNotNone(m,q)
                mask,requested,action=m.groups()
                mode=int(requested,8)&~int(mask,8)
                with tempfile.TemporaryDirectory() as folder:
                    path=Path(folder)/"file"
                    path.touch()
                    os.chmod(path,mode)
                    for op in ("g=u","o=g",action):
                        subprocess.run(["chmod",op,str(path)],check=True,stdout=subprocess.DEVNULL)
                    expected=f"0{stat.S_IMODE(path.stat().st_mode):03o}"
                self.assertEqual(item["correct"],expected)


if __name__=="__main__":
    unittest.main()
