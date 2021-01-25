from schedule.ra_sched import Day, RA
from datetime import date
import unittest


class TestDayObject(unittest.TestCase):
    def setUp(self):
        s = []
        n = 5
        for i in range(n):
            ra = RA("T","C",i,1,date(2017,1,1))
            s.append(ra)

        self.day = Day(date(2018,5,24),3,numDutySlots=n+1,ras=s)

    def test_whenProvidedRAList_setsNumDutySlotsToLengthOfProvidedList(self):
        # Test to ensure that when a list is provided as the ras parameter,
        #  the Day object sets the number of duty slots to be the length of
        #  the ra list.

        # -- Arrange --

        # The date to be used for this test
        desiredDate = date(2021, 1, 25)

        raList1 = [1]
        raList2 = [1, 2]
        raList3 = [1, 2, 3]
        raList4 = [i for i in range(43)]

        # -- Act --

        # Create the Day objects used for this test
        testDay1 = Day(desiredDate, 0, ras=raList1)
        testDay2 = Day(desiredDate, 0, ras=raList2)
        testDay3 = Day(desiredDate, 0, ras=raList3)
        testDay4 = Day(desiredDate, 0, ras=raList4)

        # -- Assert --

        # Assert that the numDutySlots attribute is updated to be the length
        #  of the provided RA list.
        self.assertEqual(testDay1.numDutySlots, len(raList1))
        self.assertEqual(testDay2.numDutySlots, len(raList2))
        self.assertEqual(testDay3.numDutySlots, len(raList3))
        self.assertEqual(testDay4.numDutySlots, len(raList4))

    def test_whenIteratingOverDayObject_iteratesOverRAsOnDuty(self):
        # Test to ensure that the __iter__ method of the Day Object
        #  iterates over the RAs that are assigned for duty on that
        #  day.

        # -- Arrange --

        # The date to be used for this test
        desiredDate = date(2021, 1, 25)

        # Create the expected RA list
        expectedRAList = []
        for i in range(25):
            expectedRAList.append(
                RA(
                    "{}".format(i),
                    "{}".format(i),
                    i,
                    1,
                    desiredDate
                )
            )

        # Create the Day object used for this test
        testDay = Day(desiredDate, 0, ras=expectedRAList)

        # -- Act/Assert --

        # Iterate over the Day object
        for i, ra in enumerate(testDay):
            # Assert that we received an RA object
            self.assertIsInstance(ra, RA)

            # Assert that the RA object that we received
            #  is the expected RA object
            self.assertEqual(expectedRAList[i], ra)

    def testAddRA(self):
        ra1 = RA("R","E",99,1,date(2017,2,2))
        ra2 = RA("C","K",98,1,date(2017,3,3))
        self.day.addDutySlot()
        preNum = self.day.numberOnDuty()

        self.day.addRA(ra1)
        self.assertEqual(self.day.numberOnDuty(),preNum+1)
        self.assertRaises(OverflowError,self.day.addRA,ra2)

    def testRemoveRA(self):
        ra = RA("D","B",97,1,date(2017,4,4))
        self.day.addDutySlot()
        self.day.addRA(ra)
        self.day.removeRA(ra)

        self.assertNotIn(ra,self.day.getRAs())

    def testNumberdutySlots(self):
        self.assertEqual(self.day.numberDutySlots(),self.day.numDutySlots)

    def testAddDutySlot(self):
        numSlots = self.day.numberDutySlots()
        addNum = 2
        self.day.addDutySlot(addNum)
        self.assertEqual(self.day.numberDutySlots(),numSlots + addNum)

    def testNumberOnDuty(self):
        num = self.day.numberOnDuty()
        self.assertEqual(num,len(self.day.ras))

    def testGetRAs(self):
        ras = self.day.getRAs()
        self.assertEqual(ras,self.day.ras)

if __name__ == "__main__":
    unittest.main()
